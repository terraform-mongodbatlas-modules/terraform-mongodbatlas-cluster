# path-sync copy -n sdlc
from __future__ import annotations

import pytest

from docs import tfdocs_links

DEAD_URL = next(iter(tfdocs_links.DEAD_RESOURCE_URLS))


def _anchor(prefix: str, name: str, suffix: str = "") -> str:
    return f'- <a name="{prefix}_{name}"></a> [{name}](#{prefix}\\_{name}){suffix}'


@pytest.fixture()
def readme_section() -> str:
    lines = [
        "## Requirements\n",
        _anchor("requirement", "terraform", " (>= 1.9)"),
        "",
        _anchor("requirement", "google", " (>= 6.0)"),
        "",
        _anchor("requirement", "mongodbatlas", " (~> 2.7)"),
        "",
        "## Providers\n",
        _anchor("provider", "mongodbatlas", " (~> 2.7)"),
        "",
        _anchor("provider", "terraform"),
        "",
        "## Resources\n",
        f"- [terraform_data.region_validations]({DEAD_URL}) (resource)",
    ]
    return "\n".join(lines) + "\n"


def test_fix_readme_links_replaces_all(readme_section: str) -> None:
    result = tfdocs_links.fix_readme_links(readme_section)
    assert "[terraform](https://developer.hashicorp.com/terraform/install)" in result
    assert (
        "[google](https://registry.terraform.io/providers/hashicorp/google/latest/docs)" in result
    )
    assert (
        "[mongodbatlas](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs)"
        in result
    )
    assert (
        "[terraform](https://developer.hashicorp.com/terraform/language/resources/terraform-data)"
        in result
    )
    assert (
        "https://developer.hashicorp.com/terraform/language/resources/terraform-data) (resource)"
        in result
    )
    assert "#requirement\\_" not in result
    assert "#provider\\_" not in result
    assert "hashicorp/terraform/latest/docs/resources/data" not in result


def test_resolve_url_special_cases() -> None:
    assert (
        tfdocs_links.resolve_url("terraform", "requirement")
        == "https://developer.hashicorp.com/terraform/install"
    )
    assert (
        tfdocs_links.resolve_url("terraform", "provider")
        == "https://developer.hashicorp.com/terraform/language/resources/terraform-data"
    )


def test_resolve_url_known_org() -> None:
    url = tfdocs_links.resolve_url("mongodbatlas", "requirement")
    assert url == "https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs"


def test_resolve_url_defaults_to_hashicorp() -> None:
    url = tfdocs_links.resolve_url("aws", "requirement")
    assert url == "https://registry.terraform.io/providers/hashicorp/aws/latest/docs"


def test_no_changes_when_no_self_refs() -> None:
    content = "No terraform-docs output here.\nJust plain text."
    assert tfdocs_links.fix_readme_links(content) == content
