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


def ensure_changelog_dir(repo_root: Path) -> None:
    """Ensure .changelog directory exists with a .keep file."""
    changelog_dir = repo_root / ".changelog"
    if not changelog_dir.exists():
        changelog_dir.mkdir()
        keep_file = changelog_dir / ".keep"
        keep_file.write_text("", encoding="utf-8")
        print(f"Created {changelog_dir} directory")


def create_initial_changelog(changelog_path: Path, version: str, current_date: str) -> None:
    """Create initial CHANGELOG.md and .changelog directory for first release."""
    repo_root = changelog_path.parent
    ensure_changelog_dir(repo_root)

    content = f"""## (Unreleased)

## {version} ({current_date})

NOTES:

* module: Initial version
"""
    changelog_path.write_text(content, encoding="utf-8")
    print(f"Created CHANGELOG.md with initial version {version} ({current_date})")


def update_changelog(changelog_path: Path, version: str, current_date: str) -> None:
    """Update CHANGELOG.md with version and current date."""
    if not changelog_path.exists():
        create_initial_changelog(changelog_path, version, current_date)
        return

    content = changelog_path.read_text(encoding="utf-8")

    unreleased_pattern = r"^## \(Unreleased\)$"
    if not re.search(unreleased_pattern, content, re.MULTILINE):
        print(
            "Error: Could not find '## (Unreleased)' header in CHANGELOG.md",
            file=sys.stderr,
        )
        sys.exit(1)

    version_pattern = rf"^## {re.escape(version)} \("
    if re.search(version_pattern, content, re.MULTILINE):
        print(f"CHANGELOG.md already has {version}, no changes needed")
        return

    new_header = f"## (Unreleased)\n\n## {version} ({current_date})"
    new_content = re.sub(unreleased_pattern, new_header, content, count=1, flags=re.MULTILINE)
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
