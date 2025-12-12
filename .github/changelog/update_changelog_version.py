#!/usr/bin/env python
"""Update CHANGELOG.md with version and current date."""

import re
import sys
from datetime import datetime
from pathlib import Path


def extract_version_number(version: str) -> str:
    """Remove 'v' prefix from version string."""
    if version.startswith("v"):
        return version[1:]
    return version


def get_current_date() -> str:
    """Get current date in 'Month day, Year' format."""
    return datetime.now().strftime("%B %d, %Y")


def update_changelog(changelog_path: Path, version: str, current_date: str) -> None:
    """Update CHANGELOG.md with version and current date."""
    if not changelog_path.exists():
        print(f"Error: File not found: {changelog_path}", file=sys.stderr)
        sys.exit(1)

    content = changelog_path.read_text(encoding="utf-8")

    # Fail fast: Check for (Unreleased) header before doing anything else
    unreleased_pattern = r"^## \(Unreleased\)$"
    if not re.search(unreleased_pattern, content, re.MULTILINE):
        print(
            "Error: Could not find '## (Unreleased)' header in CHANGELOG.md",
            file=sys.stderr,
        )
        sys.exit(1)

    # Check if version already exists
    version_pattern = rf"^## {re.escape(version)} \(([^)]+)\)$"
    version_match = re.search(version_pattern, content, re.MULTILINE)

    if version_match:
        existing_date = version_match.group(1)
        # Version exists with same date - nothing to do
        if existing_date == current_date:
            print(
                f"CHANGELOG.md already has {version} with today's date, no changes needed"
            )
            return
        # Version exists with different date - update it
        old_header = f"## {version} ({existing_date})"
        new_header = f"## {version} ({current_date})"
        changelog_path.write_text(
            content.replace(old_header, new_header), encoding="utf-8"
        )
        print(
            f"Updated CHANGELOG.md: {version} date changed from {existing_date} to {current_date}"
        )
        return

    # Version doesn't exist - add it by replacing (Unreleased)
    new_header = f"## (Unreleased)\n\n## {version} ({current_date})"
    new_content = re.sub(
        unreleased_pattern, new_header, content, count=1, flags=re.MULTILINE
    )
    changelog_path.write_text(new_content, encoding="utf-8")
    print(f"Updated CHANGELOG.md: Added {version} ({current_date})")


def main() -> None:
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: update-changelog-version.py <version>", file=sys.stderr)
        sys.exit(1)

    version_with_v = sys.argv[1]
    version = extract_version_number(version_with_v)
    current_date = get_current_date()

    repo_root = Path(__file__).parent.parent.parent
    changelog_path = repo_root / "CHANGELOG.md"

    update_changelog(changelog_path, version, current_date)


if __name__ == "__main__":
    main()
