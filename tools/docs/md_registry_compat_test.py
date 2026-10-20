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


@pytest.mark.parametrize(
    ("content", "skipped"),
    [
        ("> [!NOTE]\n> > nested quote\n> > more", ["> [!NOTE]"]),
        ("> [!NOTE]", ["> [!NOTE]"]),
        ("> [!NOTE]\n>", ["> [!NOTE]"]),
        ("> [!NOTE]\n> - item one\n> - item two", ["> [!NOTE]"]),
        ("> [!NOTE]\n> ### heading\n> body", ["> [!NOTE]"]),
        ("> [!NOTE]\n> | a | b |\n> | - | - |", ["> [!NOTE]"]),
    ],
)
def test_convert_admonitions_leaves_uncollapsable_body_unchanged(
    content: str, skipped: list[str]
) -> None:
    result, converted, skipped_result = md_registry_compat.convert_admonitions_in_content(content)
    assert result == content
    assert converted == 0
    assert skipped_result == skipped


@pytest.mark.parametrize(
    "content",
    [
        "```md\n> [!NOTE]\n> body\n```\n",
        "text\n~~~\n> [!NOTE]\n> body\n~~~\n",
    ],
)
def test_convert_admonitions_leaves_alerts_inside_fences_unchanged(content: str) -> None:
    result, converted, skipped = md_registry_compat.convert_admonitions_in_content(content)
    assert result == content
    assert converted == 0
    assert skipped == []


def test_convert_admonitions_resumes_after_fence_closes() -> None:
    content = "```md\n> [!NOTE]\n> body\n```\n> [!IMPORTANT]\n> real body\n"
    result, converted, skipped = md_registry_compat.convert_admonitions_in_content(content)
    assert result == "```md\n> [!NOTE]\n> body\n```\n~> **IMPORTANT:** real body\n"
    assert converted == 1
    assert skipped == []


def test_convert_links_in_content_makes_relative_links_absolute(tmp_path: Path) -> None:
    root_dir = tmp_path.resolve()
    md_file = root_dir / "docs" / "README.md"
    md_file.parent.mkdir(parents=True)
    md_file.write_text("")

    result = md_registry_compat.convert_links_in_content(
        "[text](../README.md)", md_file, "https://github.com/org/repo", "v1.2.3", root_dir
    )

    assert result == "[text](https://github.com/org/repo/blob/v1.2.3/README.md)"


def test_process_markdown_file_composes_links_and_admonitions(tmp_path: Path) -> None:
    root_dir = tmp_path.resolve()
    md_file = root_dir / "README.md"
    md_file.write_text("> [!NOTE]\n> See the [guide](guide.md)\n")

    was_modified, num_links, num_admonitions, skipped = md_registry_compat.process_markdown_file(
        md_file, "https://github.com/org/repo", "v1.2.3", root_dir
    )

    assert was_modified is True
    assert num_links == 1
    assert num_admonitions == 1
    assert skipped == []
    assert (
        md_file.read_text()
        == "-> **NOTE:** See the [guide](https://github.com/org/repo/blob/v1.2.3/guide.md)\n"
    )


def test_process_markdown_file_dry_run_writes_nothing(tmp_path: Path) -> None:
    root_dir = tmp_path.resolve()
    md_file = root_dir / "README.md"
    content = "> [!NOTE]\n> body\n"
    md_file.write_text(content)

    was_modified, num_links, num_admonitions, skipped = md_registry_compat.process_markdown_file(
        md_file, "https://github.com/org/repo", "v1.2.3", root_dir, dry_run=True
    )

    assert was_modified is True
    assert num_links == 0
    assert num_admonitions == 1
    assert skipped == []
    assert md_file.read_text() == content
