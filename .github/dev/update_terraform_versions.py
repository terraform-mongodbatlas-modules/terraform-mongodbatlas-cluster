"""Update .terraform-versions.yaml with latest supported Terraform versions.

Fetches Terraform releases from GitHub API, filters to minor versions >= MIN_VERSION,
and updates the versions list while preserving the header.

Requires MIN_VERSION environment variable to be set.

Usage:
    MIN_VERSION=1.9 just update-terraform-versions
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from dev import REPO_ROOT

MIN_VERSION = os.environ["MIN_VERSION"]


def fetch_terraform_versions(min_version: str) -> list[str]:
    """Fetch and filter Terraform minor versions >= min_version from GitHub."""
    result = subprocess.run(
        ["gh", "api", "repos/hashicorp/terraform/releases", "--paginate", "--jq", ".[].tag_name"],
        capture_output=True,
        text=True,
        check=True,
    )

    pattern = re.compile(r"^v(\d+)\.(\d+)\.0$")
    min_major, min_minor = map(int, min_version.split("."))

    versions = set()
    for tag in result.stdout.strip().split("\n"):
        if match := pattern.match(tag):
            major, minor = int(match.group(1)), int(match.group(2))
            if major > min_major or (major == min_major and minor >= min_minor):
                versions.add(f"{major}.{minor}")

    return sorted(versions, key=lambda v: list(map(int, v.split("."))))


def update_versions_file(versions_file: Path, versions: list[str]) -> bool:
    """Update versions file preserving header. Returns True if changed."""
    content = versions_file.read_text()
    header = content[: content.index("versions:") + len("versions:")]
    new_content = header + "\n" + "\n".join(f'  - "{v}"' for v in versions) + "\n"

    if new_content == content:
        return False

    versions_file.write_text(new_content)
    return True


def main() -> None:
    versions_file = REPO_ROOT / ".terraform-versions.yaml"

    versions = fetch_terraform_versions(MIN_VERSION)
    changed = update_versions_file(versions_file, versions)

    print("Updated" if changed else "No changes needed")


if __name__ == "__main__":
    main()
