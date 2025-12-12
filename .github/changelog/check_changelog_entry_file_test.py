"""Tests for the Go changelog entry validator.

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


def assert_valid(content: str) -> None:
    """Assert that content is a valid changelog entry."""
    exit_code, stdout, stderr = _run_checker(_dedent(content))
    assert exit_code == 0
    assert "Changelog entry is valid" in stdout


def assert_invalid(content: str, message: str) -> None:
    """Assert that content is invalid with specific error message."""
    exit_code, stdout, stderr = _run_checker(_dedent(content))
    assert exit_code == 1
    assert message in stderr


def test_valid_module_prefix() -> None:
    """Test valid entry with module prefix."""
    assert_valid(
        """
        ```release-note:enhancement
        module: Add support for auto-scaling configuration
        ```
        """
    )


def test_valid_provider_slash_prefix() -> None:
    """Test valid entry with provider/ prefix and word."""
    assert_valid(
        """
        ```release-note:enhancement
        provider/mongodbatlas: Add new authentication method
        ```
        """
    )


def test_example_regular_prefix() -> None:
    """Test entry with 'example' prefix (no slash)."""
    assert_valid(
        """
        ```release-note:enhancement
        example: Add new configuration example
        ```
        """
    )


def test_example_slash_prefix() -> None:
    """Test entry with 'example/' prefix (with slash)."""
    assert_valid(
        """
        ```release-note:enhancement
        example/basic: Add basic usage example
        ```
        """
    )


def test_multiple_entries_all_valid() -> None:
    """Test that multiple valid entries all pass."""
    assert_valid(
        """
        ```release-note:enhancement
        module: Add first feature
        ```
        ```release-note:bug
        provider/mongodbatlas: Fix authentication issue
        ```
        ```release-note:breaking-change
        terraform: Update minimum version
        ```
        """
    )


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


def test_missing_colon() -> None:
    """Test entry without colon after prefix."""
    assert_invalid(
        """
        ```release-note:enhancement
        module Add feature without colon
        ```
        """
    , "entry must follow format '<prefix>: <sentence>' where prefix is one of")


def test_missing_space_after_colon() -> None:
    """Test entry without space after colon."""
    assert_invalid(
        """
        ```release-note:enhancement
        module:Add feature without space
        ```
        """
    , "entry must follow format '<prefix>: <sentence>' where prefix is one of")


def test_sentence_ends_with_period() -> None:
    """Test entry with sentence ending in period."""
    assert_invalid(
        """
        ```release-note:enhancement
        module: Add support for auto-scaling.
        ```
        """
    , "must not end with a period")


def test_empty_sentence() -> None:
    """Test entry with empty sentence after colon."""
    assert_invalid(
        """
        ```release-note:enhancement
        module:
        ```
        """
    , "entry must follow format '<prefix>: <sentence>' where prefix is one of")


def test_slash_prefix_without_word() -> None:
    """Test slash prefix without word before colon."""
    assert_invalid(
        """
        ```release-note:enhancement
        provider/: Add authentication
        ```
        """
    , "must have format")


def test_slash_prefix_with_space_instead_of_word() -> None:
    """Test slash prefix with space instead of word."""
    assert_invalid(
        """
        ```release-note:enhancement
        provider/ mongodbatlas: Add authentication
        ```
        """
    , "must have format")


def test_invalid_prefix() -> None:
    """Test entry with invalid prefix."""
    assert_invalid(
        """
        ```release-note:enhancement
        invalidprefix: Add feature
        ```
        """
    , "entry must follow format '<prefix>: <sentence>' where prefix is one of")


def test_no_prefix() -> None:
    """Test entry without any prefix."""
    assert_invalid(
        """
        ```release-note:enhancement
        This is an entry without any prefix
        ```
        """
    , "entry must follow format '<prefix>: <sentence>' where prefix is one of")


def test_multiple_spaces_after_colon() -> None:
    """Test entry with multiple spaces after colon."""
    assert_invalid(
        """
        ```release-note:enhancement
        module:  Add feature with two spaces
        ```
        """
    , "sentence must not have leading or trailing whitespace")


def test_invalid_changelog_type() -> None:
    """Test entry with invalid changelog type."""
    exit_code, stdout, stderr = _run_checker(_dedent(
        """
        ```release-note:invalid-type
        module: Some change
        ```
        """
    ))

    assert exit_code == 1
    assert "Entry 1:" in stderr
    assert "Unknown changelog type 'invalid-type'" in stderr
    assert "breaking-change" in stderr and "note" in stderr and "enhancement" in stderr and "bug" in stderr


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


def test_multiline_sentence() -> None:
    """Test entry with multiline sentence (should fail)."""
    assert_invalid(
        """
        ```release-note:enhancement
        module: Add support for multi-region clusters
        with enhanced replication
        ```
        """
    , "sentence must be single line")


def test_multiple_entries_with_format_errors() -> None:
    """Test that all format errors are shown for multiple entries."""
    exit_code, stdout, stderr = _run_checker(_dedent(
        """
        ```release-note:enhancement
        module: Add feature with period.
        ```
        ```release-note:bug
        invalidprefix: Fix something
        ```
        ```release-note:enhancement
        module:No space after colon
        ```
        """
    ))

    assert exit_code == 1
    assert "Entry 1:" in stderr
    assert "Entry 2:" in stderr
    assert "Entry 3:" in stderr
    assert "must not end with a period" in stderr
    assert "entry must follow format '<prefix>: <sentence>' where prefix is one of" in stderr


def test_multiple_entries_with_type_and_format_errors() -> None:
    """Test that both type and format errors are shown (one error per entry)."""
    exit_code, stdout, stderr = _run_checker(_dedent(
        """
        ```release-note:invalid-type
        module: Some change
        ```
        ```release-note:enhancement
        provider/: Missing word after slash
        ```
        ```release-note:another-bad-type
        example: Another change
        ```
        """
    ))

    assert exit_code == 1
    assert "Entry 1:" in stderr and "Unknown changelog type 'invalid-type'" in stderr
    assert "Entry 2:" in stderr and "must have format" in stderr
    assert "Entry 3:" in stderr and "Unknown changelog type 'another-bad-type'" in stderr
