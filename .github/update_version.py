#!/usr/bin/env python
"""Update module_version in versions.tf file."""

import re
import sys
from pathlib import Path


def extract_version_number(version: str) -> str:
    """Remove 'v' prefix from version string."""
    if version.startswith("v"):
        return version[1:]
    return version


def update_versions_tf(file_path: Path, version: str, relative_path: str) -> None:
    """Update module_version in versions.tf file."""
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    content = file_path.read_text(encoding="utf-8")

    # Replace module_version value
    pattern = r'module_version\s*=\s*"[^"]*"'
    replacement = f'module_version = "{version}"'
    new_content = re.sub(pattern, replacement, content)

    if content == new_content:
        print(
            f"Warning: No module_version found or already set to {version} in {relative_path}",
            file=sys.stderr,
        )

    file_path.write_text(new_content, encoding="utf-8")
    print(f'✓ Updated {relative_path}: module_version = "{version}"')


def main() -> None:
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: update_version.py <version>", file=sys.stderr)
        sys.exit(1)

    version_with_v = sys.argv[1]
    version = extract_version_number(version_with_v)

    repo_root = Path(__file__).parent.parent
    for version_file in repo_root.rglob("versions.tf"):
        update_versions_tf(
            version_file, version, str(version_file.relative_to(repo_root))
        )


if __name__ == "__main__":
    main()
