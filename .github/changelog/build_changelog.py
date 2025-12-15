#!/usr/bin/env python
"""Generate changelog from latest release to HEAD and update CHANGELOG.md.

This script automates changelog generation by:

1. Finding the baseline commit to compare against:
   - First, looks for the latest version tag (v*.*.*)
   - If that tag exists and has a .changelog directory at that commit, uses it as the baseline
   - If the tag exists but has no .changelog directory (version predates changelog system),
     falls back to the 'changelog-dir-created' tag
   - If no version tags exist at all, uses the 'changelog-dir-created' tag

2. Running changelog-build (HashiCorp tool) to generate entries from baseline to HEAD
   - Reads from .changelog/*.txt files added since the baseline
   - Uses templates from .github/changelog/ to format the output

3. Updating only the (Unreleased) section in CHANGELOG.md
   - Preserves all existing released version entries
   - Replaces the (Unreleased) section with newly generated content
   - Creates CHANGELOG.md if it doesn't exist

This ensures that CHANGELOG.md always reflects unreleased changes accumulated since
the last published version, without modifying historical release entries.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# Tag that marks the commit where the .changelog directory was first introduced.
# This tag must be created in the repository before using the changelog generation workflow.
CHANGELOG_DIR_CREATED_TAG = "changelog-dir-created"


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=check,
    )


def get_latest_version_tag() -> str | None:
    """Get the latest version tag (v*.*.*)."""
    try:
        result = run_command(["git", "tag", "-l", "v*.*.*", "--sort=-version:refname"])
        tags = result.stdout.strip().split("\n")
        return tags[0] if tags and tags[0] else None
    except subprocess.CalledProcessError:
        return None


def get_commit_sha(ref: str) -> str | None:
    """Get the commit SHA for a given ref."""
    try:
        result = run_command(["git", "rev-list", "-n", "1", ref])
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def get_commit_sha_or_exit(ref: str, error_context: str) -> str:
    """Get commit SHA for a ref, or exit with an error message if it fails."""
    commit_sha = get_commit_sha(ref)
    if not commit_sha:
        print(f"Error: Could not resolve {error_context}", file=sys.stderr)
        sys.exit(1)
    return commit_sha


def changelog_exists_at_commit(commit_sha: str) -> bool:
    """Check if .changelog directory exists at a given commit."""
    try:
        result = run_command(["git", "ls-tree", commit_sha, ".changelog"])
        return bool(result.stdout.strip())
    except subprocess.CalledProcessError:
        return False


def get_changelog_dir_created_commit(reason: str) -> str:
    """Get the changelog-dir-created commit SHA with informative message."""
    print(f"Using {CHANGELOG_DIR_CREATED_TAG} ({reason})", file=sys.stderr)
    return get_commit_sha_or_exit(
        CHANGELOG_DIR_CREATED_TAG, f"{CHANGELOG_DIR_CREATED_TAG} tag"
    )


def determine_last_release() -> str:
    """Determine the last release reference for changelog generation."""
    latest_tag = get_latest_version_tag()

    # No version tags found, use changelog-dir-created tag
    if not latest_tag:
        return get_changelog_dir_created_commit("no version tags found")

    # Resolve latest tag to commit SHA
    last_release = get_commit_sha_or_exit(latest_tag, f"commit for tag {latest_tag}")

    # If .changelog exists at that commit, use it
    if changelog_exists_at_commit(last_release):
        return last_release

    # Latest tag predates changelog system, fall back to changelog-dir-created
    return get_changelog_dir_created_commit(
        f"latest tag {latest_tag} has no .changelog"
    )


def get_gopath() -> str:
    """Get the GOPATH environment variable."""
    try:
        result = run_command(["go", "env", "GOPATH"])
        gopath = result.stdout.strip()
        if not gopath:
            raise subprocess.CalledProcessError(1, ["go", "env", "GOPATH"])
        return gopath
    except subprocess.CalledProcessError:
        print("Error: Could not get GOPATH", file=sys.stderr)
        sys.exit(1)


def build_changelog(last_release: str, repo_dir: Path) -> str:
    """Run changelog-build and return the output."""
    gopath = get_gopath()
    changelog_build = Path(gopath) / "bin" / "changelog-build"

    cmd = [
        str(changelog_build),
        "-this-release",
        "HEAD",
        "-last-release",
        last_release,
        "-git-dir",
        ".",
        "-entries-dir",
        ".changelog",
        "-changelog-template",
        ".github/changelog/changelog.tmpl",
        "-note-template",
        ".github/changelog/release-note.tmpl",
    ]

    try:
        # Change to repo directory before running the command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=repo_dir,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running changelog-build: {e}", file=sys.stderr)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        sys.exit(1)


def build_changelog_content(
    new_content: str, preamble: str = "", released_versions: str = ""
) -> str:
    """Build the complete changelog content with unreleased section."""
    stripped_content = new_content.strip()
    unreleased_section = f"## (Unreleased)\n\n{stripped_content}\n"

    if not released_versions:
        # No released versions yet
        if preamble:
            return f"{preamble}\n\n{unreleased_section}"
        return unreleased_section

    # Has released versions
    if preamble:
        return f"{preamble}\n\n{unreleased_section}\n{released_versions}"
    return f"{unreleased_section}\n{released_versions}"


def find_header_index(lines: list[str], start_idx: int = 0) -> int | None:
    """Find the index of the first line starting with '## '."""
    for i in range(start_idx, len(lines)):
        if lines[i].startswith("## "):
            return i
    return None


def update_unreleased_section(
    changelog_file: Path, new_unreleased_content: str
) -> None:
    """Update only the (Unreleased) section in CHANGELOG.md."""
    # Create new file if it doesn't exist
    if not changelog_file.exists():
        content = build_changelog_content(new_unreleased_content)
        changelog_file.write_text(content, encoding="utf-8")
        return

    # Read and parse existing changelog
    existing_content = changelog_file.read_text(encoding="utf-8")
    lines = existing_content.split("\n")

    first_header_idx = find_header_index(lines)

    # No headers found, write fresh content
    if first_header_idx is None:
        content = build_changelog_content(new_unreleased_content)
        changelog_file.write_text(content, encoding="utf-8")
        return

    # Find second header (first released version)
    second_header_idx = find_header_index(lines, first_header_idx + 1)

    # Extract sections
    preamble = "\n".join(lines[:first_header_idx]).strip()
    released_versions = (
        "\n".join(lines[second_header_idx:]) if second_header_idx else ""
    )

    # Build and write new content
    new_content = build_changelog_content(
        new_unreleased_content, preamble, released_versions
    )
    changelog_file.write_text(new_content, encoding="utf-8")


def main() -> None:
    """Main function to generate and update CHANGELOG.md."""
    # Determine repository root (where the script is run from)
    repo_dir = Path.cwd()

    # Determine last release reference
    last_release = determine_last_release()

    # Generate changelog for unreleased changes
    changelog_output = build_changelog(last_release, repo_dir)

    changelog_file = repo_dir / "CHANGELOG.md"

    if changelog_output.strip():
        # Update the (Unreleased) section
        update_unreleased_section(changelog_file, changelog_output)
        print("CHANGELOG.md updated successfully", file=sys.stderr)
    else:
        print("No changelog entries found", file=sys.stderr)


if __name__ == "__main__":
    main()
