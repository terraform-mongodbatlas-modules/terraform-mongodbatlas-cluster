"""Generate complete GitHub release body from CHANGELOG.md and git repository info."""

import re
import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).parent.parent)
)  # TODO: this should rely on PYTHONPATH set instead, like in other scripts
from tf_registry_source import (
    compute_registry_source,
    get_git_remote_url,
    parse_github_repo,
)


def extract_version_section(changelog_path: Path, version: str) -> str:
    """Extract changelog section for a specific version."""
    version_without_v = version.removeprefix("v")
    content = changelog_path.read_text(encoding="utf-8")

    pattern = rf"^## {re.escape(version_without_v)} \([^)]+\)\s*\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if not match:  # this should raise a ValueError if not found
        return ""
    return match.group(1).strip()


def get_github_repo_url() -> tuple[str, str, str]:
    """Get GitHub URL, owner, and repo name from git remote."""
    remote_url = get_git_remote_url()
    owner, repo_name = parse_github_repo(remote_url)
    return f"https://github.com/{owner}/{repo_name}", owner, repo_name


def generate_release_body(version: str, changelog_path: Path) -> str:
    """Generate complete GitHub release body."""
    version_without_v = version.removeprefix("v")
    github_url, owner, repo_name = get_github_repo_url()
    registry_source = compute_registry_source(owner, repo_name)
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
        changelog_section if changelog_section else "_No changelog entries found._",
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
