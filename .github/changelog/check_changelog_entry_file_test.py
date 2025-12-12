"""Tests for the changelog entry validator.

This module tests the Go script that validates changelog entry files
to ensure they follow the required format with proper types and prefixes.
"""

from __future__ import annotations

import subprocess
import tempfile
import textwrap
from pathlib import Path

# Go script directory relative to this test file
CHECKER_DIR = Path(__file__).parent / "check-changelog-entry-file"


def _dedent(s: str) -> str:
    """Helper to dedent test strings."""
    return textwrap.dedent(s).lstrip("\n")


def _run_checker(content: str) -> tuple[int, str, str]:
    """Run the Go changelog checker with the given content.

    Writes content to a temporary file and passes the filepath to the Go script.

    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(content)
        filepath = f.name

    try:
        result = subprocess.run(
            ["go", "run", ".", filepath],
            capture_output=True,
            text=True,
            cwd=CHECKER_DIR,
        )
        return result.returncode, result.stdout, result.stderr
    finally:
        # Clean up the temp file
        Path(filepath).unlink(missing_ok=True)


def test_valid_enhancement_with_module_prefix() -> None:
    """Test valid enhancement entry with module prefix."""
    content = _dedent(
        """
        ```release-note:enhancement
        module: Add support for auto-scaling configuration
        ```
        """
    )

    exit_code, stdout, stderr = _run_checker(content)

    assert exit_code == 0
    assert "Changelog entry is valid" in stdout


def test_valid_bug_with_module_prefix() -> None:
    """Test valid bug entry with module prefix."""
    content = _dedent(
        """
        ```release-note:bug
        module: Fix validation error in cluster configuration
        ```
        """
    )

    exit_code, stdout, stderr = _run_checker(content)

    assert exit_code == 0
    assert "Changelog entry is valid" in stdout


def test_valid_note_without_required_prefix() -> None:
    """Test valid note entry (doesn't require prefix)."""
    content = _dedent(
        """
        ```release-note:note
        This is a general note that doesn't require a prefix
        ```
        """
    )

    exit_code, stdout, stderr = _run_checker(content)

    assert exit_code == 0
    assert "Changelog entry is valid" in stdout


def test_invalid_changelog_type() -> None:
    """Test entry with invalid changelog type."""
    content = _dedent(
        """
        ```release-note:invalid-type
        module: Some change
        ```
        """
    )

    exit_code, stdout, stderr = _run_checker(content)

    assert exit_code == 1
    assert "Unknown changelog types [invalid-type]" in stderr
    assert "breaking-change note enhancement bug" in stderr


def test_bug_without_required_prefix() -> None:
    """Test bug entry without required prefix."""
    content = _dedent(
        """
        ```release-note:bug
        This is a bug fix without proper prefix
        ```
        """
    )

    exit_code, stdout, stderr = _run_checker(content)

    assert exit_code == 1
    assert "incorrect prefix" in stderr.lower()
    assert "module" in stderr


def test_enhancement_without_required_prefix() -> None:
    """Test enhancement entry without required prefix."""
    content = _dedent(
        """
        ```release-note:enhancement
        Added a new feature without prefix
        ```
        """
    )

    exit_code, stdout, stderr = _run_checker(content)

    assert exit_code == 1
    assert "incorrect prefix" in stderr.lower()


def test_empty_content() -> None:
    """Test with empty content."""
    content = ""

    exit_code, stdout, stderr = _run_checker(content)

    assert exit_code == 1
    assert "no changelog entry found" in stderr.lower()


def test_no_changelog_entry_found() -> None:
    """Test with content that has no proper changelog entry format."""
    content = "This is just plain text without changelog format"

    exit_code, stdout, stderr = _run_checker(content)

    assert exit_code == 1
    assert "no changelog entry found" in stderr.lower()


def test_breaking_change_with_module_prefix() -> None:
    """Test valid breaking-change entry with module prefix."""
    content = _dedent(
        """
        ```release-note:breaking-change
        module: Remove deprecated API endpoint
        ```
        """
    )

    exit_code, stdout, stderr = _run_checker(content)

    assert exit_code == 0
    assert "Changelog entry is valid" in stdout


def test_valid_provider_prefix() -> None:
    """Test valid entry with provider/ prefix."""
    content = _dedent(
        """
        ```release-note:enhancement
        provider/: Add new authentication method
        ```
        """
    )

    exit_code, stdout, stderr = _run_checker(content)

    assert exit_code == 0
    assert "Changelog entry is valid" in stdout


def test_nonexistent_file() -> None:
    """Test with a nonexistent file."""
    nonexistent_path = "/tmp/nonexistent_changelog_file_12345.txt"

    result = subprocess.run(
        ["go", "run", ".", nonexistent_path],
        capture_output=True,
        text=True,
        cwd=CHECKER_DIR,
    )

    assert result.returncode == 0
    assert "No changelog entry file found" in result.stdout
