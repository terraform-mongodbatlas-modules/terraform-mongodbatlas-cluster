"""Validate version format and check if it already exists."""

import re
import subprocess
import sys


def validate_version_format(version: str) -> bool:
    pattern = r"^v\d+\.\d+\.\d+$"
    return bool(re.match(pattern, version))


def check_tag_exists(version: str) -> bool:
    try:
        subprocess.run(["git", "rev-parse", version], capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def check_remote_branch_exists(version: str) -> bool:
    try:
        subprocess.run(["git", "rev-parse", f"origin/{version}"], capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: validate_version.py <version>", file=sys.stderr)
        sys.exit(1)
    version = sys.argv[1]
    if not validate_version_format(version):
        print(
            f"Error: Version '{version}' must be in format vX.Y.Z (e.g., v1.0.0)",
            file=sys.stderr,
        )
        sys.exit(1)
    if check_tag_exists(version):
        print(f"Error: Tag {version} already exists", file=sys.stderr)
        sys.exit(1)
    if check_remote_branch_exists(version):
        print(f"Error: Branch {version} already exists on remote", file=sys.stderr)
        sys.exit(1)
    print(f"ok Version {version} is valid and available")


if __name__ == "__main__":
    main()
