from __future__ import annotations

from pathlib import Path

import pytest

from docs import md_registry_compat


@pytest.mark.parametrize(
    ("content", "expected", "converted"),
    [
        ("> [!NOTE]\n> body", "-> **NOTE:** body", 1),
        ("> [!TIP]\n> body", "-> **TIP:** body", 1),
        ("> [!IMPORTANT]\n> body", "~> **IMPORTANT:** body", 1),
        (
            "> [!WARNING]\n> line one\n> line two\n> line three",
            "~> **WARNING:** line one line two line three",
            1,
        ),
        ("> [!CAUTION]\n> body", "~> **CAUTION:** body", 1),
        ("> [!NOTE]\n> body\n>", "-> **NOTE:** body", 1),
        ("> quoted text", "> quoted text", 0),
        ("-> **NOTE:** body", "-> **NOTE:** body", 0),
        (
            "> [!NOTE]\n> has `code` and a [link](x.md)",
            "-> **NOTE:** has `code` and a [link](x.md)",
            1,
        ),
    ],
)
def test_convert_admonitions_in_content(content: str, expected: str, converted: int) -> None:
    result, converted_count, skipped = md_registry_compat.convert_admonitions_in_content(content)
    assert result == expected
    assert converted_count == converted
    assert skipped == []


def test_convert_admonitions_leaves_multiparagraph_unchanged() -> None:
    content = "> [!NOTE]\n> first paragraph\n>\n> second paragraph"
    result, converted, skipped = md_registry_compat.convert_admonitions_in_content(content)
    assert result == content
    assert converted == 0
    assert skipped == ["> [!NOTE]"]


def test_convert_links_in_content_makes_relative_links_absolute(tmp_path: Path) -> None:
    root_dir = tmp_path.resolve()
    md_file = root_dir / "docs" / "README.md"
    md_file.parent.mkdir(parents=True)
    md_file.write_text("")

    result = md_registry_compat.convert_links_in_content(
        "[text](../README.md)", md_file, "https://github.com/org/repo", "v1.2.3", root_dir
    )

    assert result == "[text](https://github.com/org/repo/blob/v1.2.3/README.md)"
