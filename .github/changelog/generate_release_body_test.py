from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from changelog import generate_release_body as mod


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


def test_generate_release_body(tmp_path: Path, monkeypatch) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(
        _dedent("""
        ## (Unreleased)

        ## 0.2.0 (December 17, 2025)

        * New feature
    """),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        mod,
        "get_github_repo_url",
        lambda: (
            "https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster",
            "terraform-mongodbatlas-modules",
            "terraform-mongodbatlas-cluster",
        ),
    )

    body = mod.generate_release_body("v0.2.0", changelog)

    assert 'source  = "terraform-mongodbatlas-modules/cluster/mongodbatlas"' in body
    assert 'version = "0.2.0"' in body
    assert "## What's Changed" in body
    assert "* New feature" in body
    assert "/blob/v0.2.0/README.md" in body
