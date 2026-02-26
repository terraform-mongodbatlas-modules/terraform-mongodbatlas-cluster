from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from changelog import generate_release_body as mod
from release import tf_registry_source


def _dedent(s: str) -> str:
    return textwrap.dedent(s).lstrip("\n")


def test_extract_version_section(tmp_path: Path) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(
        _dedent("""
        ## (Unreleased)

        * Future feature

        ## 0.2.0 (December 17, 2025)

        ENHANCEMENTS:

        * Added new feature ([#1](https://example.com))

        BUG FIXES:

        * Fixed a bug ([#2](https://example.com))

        ## 0.1.0 (October 31, 2025)

        * Initial release
    """),
        encoding="utf-8",
    )
    section = mod.extract_version_section(changelog, "v0.2.0")
    assert "Added new feature" in section
    assert "Fixed a bug" in section
    assert "Initial release" not in section
    assert "Future feature" not in section


def test_extract_version_section_not_found(tmp_path: Path) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text("## 0.1.0 (October 31, 2025)\n\n* Initial\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Version v0.9.0 not found"):
        mod.extract_version_section(changelog, "v0.9.0")


@pytest.mark.parametrize(
    ("repo_name", "registry_source", "expected_module_name"),
    [
        (
            "terraform-mongodbatlas-cluster",
            "terraform-mongodbatlas-modules/cluster/mongodbatlas",
            "cluster",
        ),
        (
            "terraform-mongodbatlas-atlas-gcp",
            "terraform-mongodbatlas-modules/atlas-gcp/mongodbatlas",
            "atlas_gcp",
        ),
    ],
)
def test_generate_release_body(
    tmp_path: Path, monkeypatch, repo_name: str, registry_source: str, expected_module_name: str
) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(
        _dedent("""
        ## (Unreleased)

        ## 0.2.0 (December 17, 2025)

        * New feature
    """),
        encoding="utf-8",
    )
    owner = "terraform-mongodbatlas-modules"
    monkeypatch.setattr(
        tf_registry_source,
        "get_github_repo_info",
        lambda: (f"https://github.com/{owner}/{repo_name}", owner, repo_name),
    )
    monkeypatch.setattr(tf_registry_source, "get_registry_source", lambda: registry_source)
    monkeypatch.setattr(tf_registry_source, "get_module_name", lambda: expected_module_name)
    body = mod.generate_release_body("v0.2.0", changelog)
    assert f'source  = "{registry_source}"' in body
    assert f'module "{expected_module_name}" {{' in body
    assert 'version = "0.2.0"' in body
    assert "## What's Changed" in body
    assert "* New feature" in body
    assert "/blob/v0.2.0/README.md" in body
