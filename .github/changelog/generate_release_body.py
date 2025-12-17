"""Generate complete GitHub release body from CHANGELOG.md and git repository info."""

import re
import sys
from pathlib import Path

from tf_registry_source import get_github_repo_info, get_registry_source


def extract_version_section(changelog_path: Path, version: str) -> str:
    """Extract changelog section for a specific version."""
    version_without_v = version.removeprefix("v")
    content = changelog_path.read_text(encoding="utf-8")

    pattern = rf"^## {re.escape(version_without_v)} \([^)]+\)\s*\n(.*?)(?=^## |\Z)"
    if match := re.search(pattern, content, re.MULTILINE | re.DOTALL):
        return match.group(1).strip()
    raise ValueError(f"Version {version} not found in {changelog_path}")


def generate_release_body(version: str, changelog_path: Path) -> str:
    """Generate complete GitHub release body."""
    version_without_v = version.removeprefix("v")
    github_url, _, _ = get_github_repo_info()
    registry_source = get_registry_source()
    changelog_section = extract_version_section(changelog_path, version)

    parts = [
        "## Installation\n",
        "```hcl",
        'module "cluster" {',
        f'  source  = "{registry_source}"',
        f'  version = "{version_without_v}"',
        "  # Your configuration here",
        "}",
        "```\n",
        "## What's Changed\n",
        changelog_section,
        "\n## Documentation\n",
        f"- [Terraform Registry](https://registry.terraform.io/modules/{registry_source}/{version_without_v})",
        f"- [README]({github_url}/blob/{version}/README.md)",
        f"- [Examples]({github_url}/tree/{version}/examples/)",
        f"- [CHANGELOG]({github_url}/blob/{version}/CHANGELOG.md)",
    ]
    return "\n".join(parts)


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: generate_release_body.py <version>", file=sys.stderr)
        sys.exit(1)

    version = sys.argv[1]
    repo_root = Path(__file__).parent.parent.parent
    changelog_path = repo_root / "CHANGELOG.md"

    if not changelog_path.exists():
        print(f"Error: CHANGELOG.md not found at {changelog_path}", file=sys.stderr)
        sys.exit(1)

    print(generate_release_body(version, changelog_path))


if __name__ == "__main__":
    main()
