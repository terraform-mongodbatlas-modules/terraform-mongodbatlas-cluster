"""Update .terraform-versions.yaml with latest supported Terraform versions.

Fetches Terraform releases from GitHub API, filters to minor versions >= MIN_VERSION,
and updates the versions list in .terraform-versions.yaml while preserving the header.

Usage:
    uv run --directory .github python -m dev.update_terraform_versions
    # or via just:
    just update-terraform-versions
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from urllib.request import Request, urlopen

MIN_VERSION = os.environ.get("MIN_VERSION", "1.9")
GITHUB_API_URL = "https://api.github.com/repos/hashicorp/terraform/releases"


def parse_version(version_str: str) -> tuple[int, int]:
    """Parse a version string like '1.9' into a tuple of integers."""
    parts = version_str.split(".")
    return int(parts[0]), int(parts[1])


def version_gte(version: str, min_version: str) -> bool:
    """Check if version >= min_version using numeric comparison."""
    v = parse_version(version)
    m = parse_version(min_version)
    return v[0] > m[0] or (v[0] == m[0] and v[1] >= m[1])


def fetch_releases() -> list[dict]:
    """Fetch all releases from GitHub API with pagination."""
    releases = []
    page = 1
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")

    while True:
        url = f"{GITHUB_API_URL}?per_page=100&page={page}"
        request = Request(url)
        request.add_header("Accept", "application/vnd.github+json")
        if token:
            request.add_header("Authorization", f"Bearer {token}")

        with urlopen(request) as response:
            import json

            page_releases = json.loads(response.read().decode())

        if not page_releases:
            break

        releases.extend(page_releases)
        page += 1

    return releases


def extract_minor_versions(releases: list[dict]) -> list[str]:
    """Extract minor versions from .0 releases (e.g., 'v1.9.0' -> '1.9')."""
    pattern = re.compile(r"^v(\d+\.\d+)\.0$")
    versions = set()

    for release in releases:
        tag = release.get("tag_name", "")
        match = pattern.match(tag)
        if match:
            versions.add(match.group(1))

    return list(versions)


def filter_and_sort_versions(versions: list[str], min_version: str) -> list[str]:
    """Filter versions >= min_version and sort numerically."""
    filtered = [v for v in versions if version_gte(v, min_version)]
    return sorted(filtered, key=parse_version)


def update_versions_file(versions: list[str], file_path: Path) -> bool:
    """Update .terraform-versions.yaml preserving header, return True if changed."""
    content = file_path.read_text()
    lines = content.splitlines()

    # Find the 'versions:' line and preserve everything before it (including it)
    header_lines = []
    for i, line in enumerate(lines):
        header_lines.append(line)
        if line.strip().startswith("versions:"):
            break

    # Build new content
    new_lines = header_lines + [f'  - "{v}"' for v in versions]
    new_content = "\n".join(new_lines) + "\n"

    if new_content == content:
        return False

    file_path.write_text(new_content)
    return True


def main() -> int:
    """Main function to update Terraform versions."""
    repo_root = Path(__file__).parent.parent.parent
    versions_file = repo_root / ".terraform-versions.yaml"

    if not versions_file.exists():
        print(f"Error: {versions_file} not found", file=sys.stderr)
        return 1

    print("Fetching Terraform releases from GitHub API...", file=sys.stderr)
    releases = fetch_releases()
    print(f"Found {len(releases)} releases", file=sys.stderr)

    minor_versions = extract_minor_versions(releases)
    print(f"Extracted {len(minor_versions)} minor versions", file=sys.stderr)

    versions = filter_and_sort_versions(minor_versions, MIN_VERSION)
    print(f"Filtered to {len(versions)} versions >= {MIN_VERSION}: {versions}", file=sys.stderr)

    changed = update_versions_file(versions, versions_file)

    if changed:
        print(f"Updated {versions_file}", file=sys.stderr)
    else:
        print("No changes needed", file=sys.stderr)

    # Output versions as JSON for workflow consumption
    import json

    print(json.dumps(versions))

    return 0


if __name__ == "__main__":
    sys.exit(main())
