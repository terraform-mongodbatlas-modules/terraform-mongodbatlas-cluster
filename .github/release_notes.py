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


def generate_release_notes_api(
    repo: str, current_version: str, previous_tag: str, target_branch: str
) -> str:
    """Generate release notes using GitHub API."""
    result = subprocess.run(
        [
            "gh",
            "api",
            f"repos/{repo}/releases/generate-notes",
            "-f",
            f"tag_name={current_version}",
            "-f",
            f"target_commitish={target_branch}",
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
    if len(sys.argv) != 2:
        print("Usage: release_notes.py <version>", file=sys.stderr)
        print("Example: release_notes.py v1.0.0", file=sys.stderr)
        sys.exit(1)

    current_version = sys.argv[1]

    # Get repository information
    repo = get_repo_name()
    print(f"Generating release notes for {current_version}...", file=sys.stderr)

    # Find previous release
    previous_tag = get_previous_tag(current_version)

    if not previous_tag:
        print("No previous release found - this is the first release", file=sys.stderr)
        print("Initial release of terraform-mongodbatlas-cluster module.")
        return

    print(f"Comparing {previous_tag} → {current_version}", file=sys.stderr)

    # Generate release notes via GitHub API (compares the two tags directly)
    notes = generate_release_notes_api(
        repo, current_version, previous_tag, current_version
    )
    print(notes)


if __name__ == "__main__":
    main()
