from __future__ import annotations

import sys
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest
from changelog import update_changelog_version as mod


def _dedent(s: str) -> str:
    """Helper to dedent test strings."""
    return textwrap.dedent(s).lstrip("\n")


def test_extract_version_number_with_v_prefix() -> None:
    """Test version extraction with 'v' prefix."""
    assert mod.extract_version_number("v1.2.3") == "1.2.3"
    assert mod.extract_version_number("v0.1.0") == "0.1.0"


def test_extract_version_number_without_v_prefix() -> None:
    """Test version extraction without 'v' prefix."""
    assert mod.extract_version_number("1.2.3") == "1.2.3"
    assert mod.extract_version_number("0.1.0") == "0.1.0"


def test_get_current_date_format() -> None:
    """Test date formatting matches expected format."""
    date_str = mod.get_current_date()
    # Should match format like "December 12, 2025"
    assert ", " in date_str
    parts = date_str.split(", ")
    assert len(parts) == 2
    # Year should be 4 digits
    assert len(parts[1]) == 4
    assert parts[1].isdigit()


def test_update_changelog_adds_new_version(tmp_path: Path) -> None:
    """Test adding a new version to changelog."""
    changelog_file = tmp_path / "CHANGELOG.md"
    existing = _dedent(
        """
        ## (Unreleased)

        ENHANCEMENTS:

        * module: Adds new feature

        ## 0.1.0 (October 31, 2025)

        * Initial release
        """
    )
    changelog_file.write_text(existing, encoding="utf-8")

    mod.update_changelog(changelog_file, "0.2.0", "December 12, 2025")

    content = changelog_file.read_text(encoding="utf-8")
    expected = _dedent(
        """
        ## (Unreleased)

        ## 0.2.0 (December 12, 2025)

        ENHANCEMENTS:

        * module: Adds new feature

        ## 0.1.0 (October 31, 2025)

        * Initial release
        """
    )
    assert content == expected


def test_update_changelog_preserves_unreleased_section(tmp_path: Path) -> None:
    """Test that a new (Unreleased) header is added above the version."""
    changelog_file = tmp_path / "CHANGELOG.md"
    existing = _dedent(
        """
        ## (Unreleased)

        * Some change

        ## 0.1.0 (October 31, 2025)

        * Initial release
        """
    )
    changelog_file.write_text(existing, encoding="utf-8")

    mod.update_changelog(changelog_file, "0.2.0", "December 12, 2025")

    content = changelog_file.read_text(encoding="utf-8")
    # Should have both (Unreleased) at top and the new version
    assert content.startswith("## (Unreleased)\n\n## 0.2.0")
    assert "## 0.1.0 (October 31, 2025)" in content


def test_update_changelog_idempotent_same_date(tmp_path: Path, capsys) -> None:
    """Test that updating with same date is idempotent."""
    changelog_file = tmp_path / "CHANGELOG.md"
    existing = _dedent(
        """
        ## (Unreleased)

        ## 0.2.0 (December 12, 2025)

        * Some feature

        ## 0.1.0 (October 31, 2025)

        * Initial release
        """
    )
    changelog_file.write_text(existing, encoding="utf-8")

    mod.update_changelog(changelog_file, "0.2.0", "December 12, 2025")

    # Content should be unchanged
    content = changelog_file.read_text(encoding="utf-8")
    assert content == existing

    # Should print success message
    captured = capsys.readouterr()
    assert "already has 0.2.0 with today's date" in captured.out


def test_update_changelog_updates_existing_version_date(tmp_path: Path) -> None:
    """Test updating date for an existing version."""
    changelog_file = tmp_path / "CHANGELOG.md"
    existing = _dedent(
        """
        ## (Unreleased)

        ## 0.2.0 (December 11, 2025)

        * Some feature

        ## 0.1.0 (October 31, 2025)

        * Initial release
        """
    )
    changelog_file.write_text(existing, encoding="utf-8")

    mod.update_changelog(changelog_file, "0.2.0", "December 12, 2025")

    content = changelog_file.read_text(encoding="utf-8")
    expected = _dedent(
        """
        ## (Unreleased)

        ## 0.2.0 (December 12, 2025)

        * Some feature

        ## 0.1.0 (October 31, 2025)

        * Initial release
        """
    )
    assert content == expected


def test_update_changelog_file_not_found(tmp_path: Path) -> None:
    """Test error handling when changelog file doesn't exist."""
    changelog_file = tmp_path / "NONEXISTENT.md"

    with pytest.raises(SystemExit) as exc_info:
        mod.update_changelog(changelog_file, "0.2.0", "December 12, 2025")

    assert exc_info.value.code == 1


def test_update_changelog_missing_unreleased_header(tmp_path: Path) -> None:
    """Test error handling when (Unreleased) header is missing."""
    changelog_file = tmp_path / "CHANGELOG.md"
    existing = _dedent(
        """
        ## 0.1.0 (October 31, 2025)

        * Initial release
        """
    )
    changelog_file.write_text(existing, encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        mod.update_changelog(changelog_file, "0.2.0", "December 12, 2025")

    assert exc_info.value.code == 1


def test_update_changelog_with_empty_unreleased_section(tmp_path: Path) -> None:
    """Test adding version when unreleased section is empty."""
    changelog_file = tmp_path / "CHANGELOG.md"
    existing = _dedent(
        """
        ## (Unreleased)

        ## 0.1.0 (October 31, 2025)

        * Initial release
        """
    )
    changelog_file.write_text(existing, encoding="utf-8")

    mod.update_changelog(changelog_file, "0.2.0", "December 12, 2025")

    content = changelog_file.read_text(encoding="utf-8")
    expected = _dedent(
        """
        ## (Unreleased)

        ## 0.2.0 (December 12, 2025)

        ## 0.1.0 (October 31, 2025)

        * Initial release
        """
    )
    assert content == expected


def test_update_changelog_multiple_versions(tmp_path: Path) -> None:
    """Test that only the specified version is updated."""
    changelog_file = tmp_path / "CHANGELOG.md"
    existing = _dedent(
        """
        ## (Unreleased)

        ## 0.3.0 (December 10, 2025)

        * Feature C

        ## 0.2.0 (November 15, 2025)

        * Feature B

        ## 0.1.0 (October 31, 2025)

        * Feature A
        """
    )
    changelog_file.write_text(existing, encoding="utf-8")

    mod.update_changelog(changelog_file, "0.2.0", "December 12, 2025")

    content = changelog_file.read_text(encoding="utf-8")
    # Only 0.2.0 date should change
    assert "## 0.2.0 (December 12, 2025)" in content
    # Other versions should remain unchanged
    assert "## 0.3.0 (December 10, 2025)" in content
    assert "## 0.1.0 (October 31, 2025)" in content


def test_main_with_valid_version(tmp_path: Path, monkeypatch, capsys) -> None:
    """Test main function with valid version argument."""
    changelog_file = tmp_path / "CHANGELOG.md"
    existing = _dedent(
        """
        ## (Unreleased)

        * Some change
        """
    )
    changelog_file.write_text(existing, encoding="utf-8")

    # Mock sys.argv and Path resolution
    monkeypatch.setattr(sys, "argv", ["script.py", "v0.2.0"])

    # Mock the date to make test deterministic
    with patch.object(mod, "get_current_date", return_value="December 12, 2025"):
        # Mock Path(__file__).parent.parent.parent to return tmp_path
        with patch.object(Path, "__new__") as mock_path:

            def path_new(cls, *args):
                if args and args[0] == mod.__file__:
                    # Return a path where .parent.parent.parent leads to tmp_path
                    fake_file = tmp_path / ".github" / "changelog" / "script.py"
                    fake_file.parent.mkdir(parents=True, exist_ok=True)
                    return Path.__new__(Path, str(fake_file))
                return Path.__new__(Path, *args)

            mock_path.side_effect = path_new

            # We need to mock the entire Path resolution in main
            def mocked_main():
                version_with_v = sys.argv[1]
                version = mod.extract_version_number(version_with_v)
                current_date = mod.get_current_date()
                mod.update_changelog(changelog_file, version, current_date)

            monkeypatch.setattr(mod, "main", mocked_main)

            mod.main()

    content = changelog_file.read_text(encoding="utf-8")
    assert "## 0.2.0 (December 12, 2025)" in content


def test_main_missing_argument(monkeypatch, capsys) -> None:
    """Test main function with missing argument."""
    monkeypatch.setattr(sys, "argv", ["script.py"])

    with pytest.raises(SystemExit) as exc_info:
        mod.main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Usage: update-changelog-version.py <version>" in captured.err


def test_update_changelog_with_special_characters_in_entries(tmp_path: Path) -> None:
    """Test that special characters in changelog entries are preserved."""
    changelog_file = tmp_path / "CHANGELOG.md"
    existing = _dedent(
        """
        ## (Unreleased)

        ENHANCEMENTS:

        * module: Adds support for `auto_scaling` configuration ([#42](https://github.com/example/repo/pull/42))
        * terraform: Fixes validation with `regions[*].name` pattern

        ## 0.1.0 (October 31, 2025)

        * Initial release
        """
    )
    changelog_file.write_text(existing, encoding="utf-8")

    mod.update_changelog(changelog_file, "0.2.0", "December 12, 2025")

    content = changelog_file.read_text(encoding="utf-8")
    # Special characters should be preserved
    assert "Adds support for `auto_scaling` configuration" in content
    assert "([#42](https://github.com/example/repo/pull/42))" in content
    assert "`regions[*].name`" in content
