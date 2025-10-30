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


def update_versions_tf(file_path: Path, version: str) -> None:
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
            f"Warning: No module_version found or already set to {version}",
            file=sys.stderr,
        )

    file_path.write_text(new_content, encoding="utf-8")
    print(f'✓ Updated versions.tf: module_version = "{version}"')


def main() -> None:
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: update_version.py <version>", file=sys.stderr)
        sys.exit(1)

    version_with_v = sys.argv[1]
    version = extract_version_number(version_with_v)

    # Assume we're in the repo root
    versions_file = Path("versions.tf")
    update_versions_tf(versions_file, version)


if __name__ == "__main__":
    main()
