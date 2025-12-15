from __future__ import annotations

import textwrap
from pathlib import Path

from changelog import build_changelog as mod


def _dedent(s: str) -> str:
    """Helper to dedent test strings."""
    return textwrap.dedent(s).lstrip("\n")


def test_update_unreleased_section_creates_new_file(tmp_path: Path) -> None:
    """Test creating a new CHANGELOG.md when it doesn't exist."""
    changelog_file = tmp_path / "CHANGELOG.md"
    new_content = "* Added new feature\n* Fixed bug"

    mod.update_unreleased_section(changelog_file, new_content)

    assert changelog_file.exists()
    content = changelog_file.read_text(encoding="utf-8")
    assert content == "## (Unreleased)\n\n* Added new feature\n* Fixed bug\n"


def test_update_unreleased_section_no_headers_creates_unreleased(
    tmp_path: Path,
) -> None:
    """Test creating unreleased section when file has no headers."""
    changelog_file = tmp_path / "CHANGELOG.md"
    changelog_file.write_text("Some preamble text\n", encoding="utf-8")

    new_content = "* Added new feature"

    mod.update_unreleased_section(changelog_file, new_content)

    content = changelog_file.read_text(encoding="utf-8")
    assert content == "## (Unreleased)\n\n* Added new feature\n"


def test_update_unreleased_section_only_unreleased_header(tmp_path: Path) -> None:
    """Test updating when only unreleased section exists."""
    changelog_file = tmp_path / "CHANGELOG.md"
    existing = _dedent(
        """
        ## (Unreleased)

        * Old unreleased change
        """
    )
    changelog_file.write_text(existing, encoding="utf-8")

    new_content = "* New unreleased change"

    mod.update_unreleased_section(changelog_file, new_content)

    content = changelog_file.read_text(encoding="utf-8")
    assert content == "## (Unreleased)\n\n* New unreleased change\n"


def test_update_unreleased_section_with_released_versions(tmp_path: Path) -> None:
    """Test updating unreleased section while preserving released versions."""
    changelog_file = tmp_path / "CHANGELOG.md"
    existing = _dedent(
        """
        ## (Unreleased)

        * Old unreleased change

        ## v1.0.0

        * Released feature 1
        * Released feature 2

        ## v0.9.0

        * Initial release
        """
    )
    changelog_file.write_text(existing, encoding="utf-8")

    new_content = "* New unreleased change\n* Another new change"

    mod.update_unreleased_section(changelog_file, new_content)

    content = changelog_file.read_text(encoding="utf-8")
    expected = _dedent(
        """
        ## (Unreleased)

        * New unreleased change
        * Another new change

        ## v1.0.0

        * Released feature 1
        * Released feature 2

        ## v0.9.0

        * Initial release
        """
    )
    assert content == expected


def test_update_unreleased_section_with_preamble(tmp_path: Path) -> None:
    """Test updating unreleased section while preserving preamble text."""
    changelog_file = tmp_path / "CHANGELOG.md"
    existing = _dedent(
        """
        # Changelog

        This is the changelog for our project.

        ## (Unreleased)

        * Old unreleased change

        ## v1.0.0

        * First release
        """
    )
    changelog_file.write_text(existing, encoding="utf-8")

    new_content = "* New feature"

    mod.update_unreleased_section(changelog_file, new_content)

    content = changelog_file.read_text(encoding="utf-8")
    expected = _dedent(
        """
        # Changelog

        This is the changelog for our project.

        ## (Unreleased)

        * New feature

        ## v1.0.0

        * First release
        """
    )
    assert content == expected


def test_update_unreleased_section_strips_content(tmp_path: Path) -> None:
    """Test that new content is stripped of leading/trailing whitespace."""
    changelog_file = tmp_path / "CHANGELOG.md"

    new_content = "\n\n  * Feature with extra whitespace  \n\n"

    mod.update_unreleased_section(changelog_file, new_content)

    content = changelog_file.read_text(encoding="utf-8")
    assert content == "## (Unreleased)\n\n* Feature with extra whitespace\n"
