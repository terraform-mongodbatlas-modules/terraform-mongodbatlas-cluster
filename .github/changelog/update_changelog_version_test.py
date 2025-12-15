from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import pytest
from changelog import update_changelog_version as mod


def _dedent(s: str) -> str:
    """Helper to dedent test strings."""
    return textwrap.dedent(s).lstrip("\n")


def test_extract_version_number() -> None:
    """Test version extraction with various inputs."""
    assert mod.extract_version_number("v1.2.3") == "1.2.3"
    assert mod.extract_version_number("1.2.3") == "1.2.3"
    assert mod.extract_version_number("") == ""
    assert mod.extract_version_number("v1") == "1"


def test_get_current_date_format() -> None:
    """Test date formatting matches expected format."""
    date_str = mod.get_current_date()
    assert ", " in date_str
    parts = date_str.split(", ")
    assert len(parts) == 2
    assert len(parts[1]) == 4 and parts[1].isdigit()


def test_update_changelog_adds_new_version(tmp_path: Path) -> None:
    """Test adding a new version to changelog."""
    changelog_file = tmp_path / "CHANGELOG.md"
    changelog_file.write_text(
        _dedent("""
        ## (Unreleased)

        * Some change

        ## 0.1.0 (October 31, 2025)
        """),
        encoding="utf-8",
    )

    mod.update_changelog(changelog_file, "0.2.0", "December 12, 2025")

    content = changelog_file.read_text(encoding="utf-8")
    assert content.startswith("## (Unreleased)\n\n## 0.2.0 (December 12, 2025)")
    assert "## 0.1.0 (October 31, 2025)" in content


def test_update_changelog_version_already_exists(tmp_path: Path, capsys) -> None:
    """Test that existing versions are skipped."""
    changelog_file = tmp_path / "CHANGELOG.md"
    existing = _dedent("""
        ## (Unreleased)

        ## 0.2.0 (December 12, 2025)

        * Some feature
        """)
    changelog_file.write_text(existing, encoding="utf-8")

    mod.update_changelog(changelog_file, "0.2.0", "December 13, 2025")

    assert changelog_file.read_text(encoding="utf-8") == existing
    assert "already has 0.2.0" in capsys.readouterr().out


def test_update_changelog_file_not_found(tmp_path: Path) -> None:
    """Test error handling when changelog file doesn't exist."""
    with pytest.raises(SystemExit) as exc_info:
        mod.update_changelog(tmp_path / "NONEXISTENT.md", "0.2.0", "December 12, 2025")
    assert exc_info.value.code == 1


def test_update_changelog_missing_unreleased_header(tmp_path: Path) -> None:
    """Test error handling when (Unreleased) header is missing."""
    changelog_file = tmp_path / "CHANGELOG.md"
    changelog_file.write_text("## 0.1.0 (October 31, 2025)\n", encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        mod.update_changelog(changelog_file, "0.2.0", "December 12, 2025")
    assert exc_info.value.code == 1


def test_main_missing_argument(monkeypatch, capsys) -> None:
    """Test main function with missing argument."""
    monkeypatch.setattr(sys, "argv", ["script.py"])

    with pytest.raises(SystemExit) as exc_info:
        mod.main()

    assert exc_info.value.code == 1
    assert "Usage:" in capsys.readouterr().err
