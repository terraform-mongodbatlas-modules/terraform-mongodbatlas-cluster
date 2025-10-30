#!/usr/bin/env python
"""Generate release notes by comparing current version with previous release."""

import subprocess
import sys
from typing import Optional


def get_previous_tag(current_version: str) -> Optional[str]:
    """Get the most recent version tag before the current one."""
    try:
        result = subprocess.run(
            ["git", "tag", "-l", "v*.*.*"],
            capture_output=True,
            text=True,
            check=True,
        )

        tags = [
            tag.strip()
            for tag in result.stdout.strip().split("\n")
            if tag.strip() and tag.strip() != current_version
        ]

        if not tags:
            return None

        # Sort tags by version (semantic versioning)
        sorted_tags = sorted(
            tags,
            key=lambda t: [int(x) for x in t.lstrip("v").split(".")],
        )

        return sorted_tags[-1] if sorted_tags else None
    except (subprocess.CalledProcessError, ValueError):
        return None


def get_commit_sha(ref: str) -> Optional[str]:
    """Get commit SHA for a given ref (tag, branch, or commit)."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", ref],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def is_valid_tag(tag: str) -> bool:
    """Check if a string is a valid git tag."""
    try:
        subprocess.run(
            ["git", "rev-parse", f"refs/tags/{tag}"],
            capture_output=True,
            check=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def generate_notes_from_git_log(from_ref: str, to_ref: str) -> str:
    """Generate release notes using git log when tags don't exist."""
    try:
        from_sha = get_commit_sha(from_ref)
        to_sha = get_commit_sha(to_ref)

        if not from_sha:
            return f"Error: Could not resolve reference '{from_ref}'"
        if not to_sha:
            return f"Error: Could not resolve reference '{to_ref}'"

        # Get commit log
        result = subprocess.run(
            [
                "git",
                "log",
                f"{from_sha}..{to_sha}",
                "--pretty=format:* %s (%h)",
                "--no-merges",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        commits = result.stdout.strip()

        if not commits:
            return "No changes found between the specified commits."

        # Build release notes
        notes = "## What's Changed\n\n"
        notes += commits + "\n\n"
        notes += f"**Commits**: {from_sha[:8]}...{to_sha[:8]}\n"

        return notes
    except subprocess.CalledProcessError as e:
        print(f"Error generating notes from git log: {e}", file=sys.stderr)
        return "Unable to generate release notes."


def generate_release_notes_api(
    repo: str, current_version: str, previous_tag: str, target_ref: str
) -> str:
    """
    Generate release notes using GitHub API.

    Note: This requires the commits to exist on GitHub remote.
    If tags don't exist yet, commit SHAs are used as fallback.
    """
    # Try to use tags first, fall back to commit SHAs if needed
    current_sha = get_commit_sha(target_ref) or target_ref
    previous_sha = get_commit_sha(previous_tag) or previous_tag

    print(f"Using commits: {previous_sha[:8]} → {current_sha[:8]}", file=sys.stderr)

    result = subprocess.run(
        [
            "gh",
            "api",
            f"repos/{repo}/releases/generate-notes",
            "-f",
            f"tag_name={current_version}",
            "-f",
            f"target_commitish={current_sha}",
            "-f",
            f"previous_tag_name={previous_tag}",
            "--jq",
            ".body",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    return result.stdout.strip()


def get_repo_name() -> str:
    """Get the GitHub repository name from git remote."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
        )

        remote_url = result.stdout.strip()

        # Parse repository from URL
        # https://github.com/owner/repo.git -> owner/repo
        # git@github.com:owner/repo.git -> owner/repo
        if "github.com" in remote_url:
            parts = remote_url.replace("git@github.com:", "").replace(
                "https://github.com/", ""
            )
            return parts.rstrip(".git")

        raise ValueError(f"Could not parse GitHub repo from URL: {remote_url}")
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to get git remote: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main function to generate release notes."""
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: release_notes.py <new_version> [old_version]", file=sys.stderr)
        print("", file=sys.stderr)
        print("Examples:", file=sys.stderr)
        print(
            "  release_notes.py v1.0.0              # Auto-detect previous release",
            file=sys.stderr,
        )
        print(
            "  release_notes.py v1.1.0 v1.0.0       # Compare specific versions",
            file=sys.stderr,
        )
        print(
            "  release_notes.py v1.0.0 abc123       # Compare with specific commit",
            file=sys.stderr,
        )
        print("", file=sys.stderr)
        print("Note: This requires the commits to exist on GitHub.", file=sys.stderr)
        print("      Run after pushing the release branch and tag.", file=sys.stderr)
        sys.exit(1)

    current_version = sys.argv[1]
    previous_version = sys.argv[2] if len(sys.argv) == 3 else None

    # Get repository information
    repo = get_repo_name()
    print(f"Generating release notes for {current_version}...", file=sys.stderr)

    # Find previous release
    if previous_version:
        print(f"Using specified previous version: {previous_version}", file=sys.stderr)
        previous_tag = previous_version
    else:
        previous_tag = get_previous_tag(current_version)
        if not previous_tag:
            print(
                "No previous release found - this is the first release", file=sys.stderr
            )
            print("", file=sys.stderr)
            print("Tip: Specify a commit/tag to compare against:", file=sys.stderr)
            print(
                f"     just release-notes {current_version} <previous_commit>",
                file=sys.stderr,
            )
            print("Initial release of terraform-mongodbatlas-cluster module.")
            return

    print(f"Comparing {previous_tag} → {current_version}", file=sys.stderr)

    # Check if both are valid tags - GitHub API requires actual tags
    current_is_tag = is_valid_tag(current_version)
    previous_is_tag = is_valid_tag(previous_tag)

    if not current_is_tag or not previous_is_tag:
        # Fall back to git log for commit-to-commit comparison
        if not current_is_tag:
            print(
                f"Note: '{current_version}' is not a tag, using git log for comparison",
                file=sys.stderr,
            )
        if not previous_is_tag:
            print(
                f"Note: '{previous_tag}' is not a tag, using git log for comparison",
                file=sys.stderr,
            )

        notes = generate_notes_from_git_log(previous_tag, current_version)
        print(notes)
    else:
        # Both are tags - use GitHub API for better formatting
        try:
            notes = generate_release_notes_api(
                repo, current_version, previous_tag, current_version
            )
            print(notes)
        except subprocess.CalledProcessError as e:
            print(
                "\nError: Failed to generate release notes via GitHub API",
                file=sys.stderr,
            )
            print(
                "Make sure the commits exist on GitHub (push first).", file=sys.stderr
            )
            print(
                f"\nGitHub API error: {e.stderr if e.stderr else str(e)}",
                file=sys.stderr,
            )
            print("\nFalling back to git log...", file=sys.stderr)
            notes = generate_notes_from_git_log(previous_tag, current_version)
            print(notes)


if __name__ == "__main__":
    main()
