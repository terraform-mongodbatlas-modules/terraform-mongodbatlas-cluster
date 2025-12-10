#!/usr/bin/env python
"""Generate changelog from latest release to HEAD and update CHANGELOG.md."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=check,
    )


def get_latest_version_tag() -> Optional[str]:
    """Get the latest version tag (v*.*.*)."""
    try:
        result = run_command(
            ["git", "tag", "-l", "v*.*.*", "--sort=-version:refname"]
        )
        tags = result.stdout.strip().split("\n")
        return tags[0] if tags and tags[0] else None
    except subprocess.CalledProcessError:
        return None


def get_commit_sha(ref: str) -> Optional[str]:
    """Get the commit SHA for a given ref."""
    try:
        result = run_command(["git", "rev-list", "-n", "1", ref])
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def changelog_exists_at_commit(commit_sha: str) -> bool:
    """Check if .changelog directory exists at a given commit."""
    try:
        result = run_command(["git", "ls-tree", commit_sha, ".changelog"])
        return bool(result.stdout.strip())
    except subprocess.CalledProcessError:
        return False


def determine_last_release() -> str:
    """Determine the last release reference for changelog generation."""
    # Try to get the latest version tag
    latest_tag = get_latest_version_tag()

    if latest_tag:
        last_release = get_commit_sha(latest_tag)
        if not last_release:
            print(
                f"Error: Could not resolve commit for tag {latest_tag}",
                file=sys.stderr,
            )
            sys.exit(1)

        # Check if .changelog exists at that commit
        if not changelog_exists_at_commit(last_release):
            print(
                f"Using changelog-dir-created (latest tag {latest_tag} has no .changelog)",
                file=sys.stderr,
            )
            last_release = get_commit_sha("changelog-dir-created")
            if not last_release:
                print(
                    "Error: Could not resolve changelog-dir-created tag",
                    file=sys.stderr,
                )
                sys.exit(1)
    else:
        # No version tags found, use changelog-dir-created
        print("Using changelog-dir-created (no version tags found)", file=sys.stderr)
        last_release = get_commit_sha("changelog-dir-created")
        if not last_release:
            print(
                "Error: Could not resolve changelog-dir-created tag", file=sys.stderr
            )
            sys.exit(1)

    return last_release


def get_gopath() -> str:
    """Get the GOPATH environment variable."""
    try:
        result = run_command(["go", "env", "GOPATH"])
        return result.stdout.strip()
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


def update_unreleased_section(
    changelog_file: Path, new_unreleased_content: str
) -> None:
    """Update only the (Unreleased) section in CHANGELOG.md."""
    if not changelog_file.exists():
        # Create new CHANGELOG.md with header and unreleased section
        content = f"## (Unreleased)\n\n{new_unreleased_content.strip()}\n"
        changelog_file.write_text(content)
        return

    # Read existing changelog
    existing_content = changelog_file.read_text()
    lines = existing_content.split("\n")

    # Find the first ## (should be ## (Unreleased))
    first_header_idx = None
    for i, line in enumerate(lines):
        if line.startswith("## "):
            first_header_idx = i
            break

    if first_header_idx is None:
        # No headers found, create new file with unreleased section
        content = f"## (Unreleased)\n\n{new_unreleased_content.strip()}\n"
        changelog_file.write_text(content)
        return

    # Find the second ## (should be first released version)
    second_header_idx = None
    for i in range(first_header_idx + 1, len(lines)):
        if lines[i].startswith("## "):
            second_header_idx = i
            break

    # Build the new content
    if second_header_idx is None:
        # No released versions yet, just update unreleased section
        new_content = (
            f"## (Unreleased)\n\n{new_unreleased_content.strip()}\n"
        )
    else:
        # Keep everything from the second header onwards (released versions)
        header = "\n".join(lines[:first_header_idx])
        released_versions = "\n".join(lines[second_header_idx:])

        if header.strip():
            new_content = f"{header}\n## (Unreleased)\n\n{new_unreleased_content.strip()}\n\n{released_versions}"
        else:
            new_content = f"## (Unreleased)\n\n{new_unreleased_content.strip()}\n\n{released_versions}"

    changelog_file.write_text(new_content)


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
