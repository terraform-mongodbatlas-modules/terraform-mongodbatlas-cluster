# path-sync copy -n sdlc
"""Replace self-referencing and dead links in terraform-docs output."""

from __future__ import annotations

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

KNOWN_PROVIDER_ORGS: dict[str, str] = {
    "mongodbatlas": "mongodb",
}

TERRAFORM_SPECIAL_CASES: dict[str, dict[str, str]] = {
    "requirement": {
        "terraform": "https://developer.hashicorp.com/terraform/install",
    },
    "provider": {
        "terraform": "https://developer.hashicorp.com/terraform/language/resources/terraform-data",
    },
}

DEAD_RESOURCE_URLS: dict[str, str] = {
    "https://registry.terraform.io/providers/hashicorp/terraform/latest/docs/resources/data": "https://developer.hashicorp.com/terraform/language/resources/terraform-data",
}

SELF_REF_PATTERN = re.compile(
    r"\[(?P<name>[^\]]+)\]\(#(?P<prefix>requirement|provider)\\_(?P=name)\)"
)

DEFAULT_ORG = "hashicorp"


def provider_url(name: str) -> str:
    org = KNOWN_PROVIDER_ORGS.get(name, DEFAULT_ORG)
    return f"https://registry.terraform.io/providers/{org}/{name}/latest/docs"


def resolve_url(name: str, section_prefix: str) -> str:
    special = TERRAFORM_SPECIAL_CASES.get(section_prefix, {})
    return special.get(name, provider_url(name))


def replace_self_ref_links(content: str) -> str:
    def _replace(match: re.Match[str]) -> str:
        name = match.group("name")
        prefix = match.group("prefix")
        url = resolve_url(name, prefix)
        return f"[{name}]({url})"

    return SELF_REF_PATTERN.sub(_replace, content)


def replace_dead_resource_links(content: str) -> str:
    for dead_url, fixed_url in DEAD_RESOURCE_URLS.items():
        content = content.replace(dead_url, fixed_url)
    return content


def fix_readme_links(content: str) -> str:
    content = replace_self_ref_links(content)
    return replace_dead_resource_links(content)


def main() -> None:
    readme_path = Path("README.md")
    content = readme_path.read_text(encoding="utf-8")
    updated = fix_readme_links(content)
    if content == updated:
        logger.info("No link replacements needed in README.md")
        return
    readme_path.write_text(updated, encoding="utf-8")
    logger.info("Updated self-referencing and dead links in README.md")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
