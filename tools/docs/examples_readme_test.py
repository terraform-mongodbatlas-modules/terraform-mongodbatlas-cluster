from __future__ import annotations

from pathlib import Path

import pytest

from docs import examples_readme as mod


@pytest.mark.parametrize(
    ("description", "expected_content"),
    [
        ("Example description", "# Example\n\nExample description\n\n## Body"),
        ("", "# Example\n\n## Body"),
    ],
)
def test_generate_readme_description(
    tmp_path: Path, description: str, expected_content: str
) -> None:
    readme = mod.generate_readme(
        "# {{ .NAME }}\n\n{{ .DESCRIPTION }}\n\n## Body\n",
        "Example",
        tmp_path,
        "example/source",
        {},
        description=description,
    )

    assert expected_content in readme
    assert "{{ .DESCRIPTION }}" not in readme


def test_get_example_description_by_folder_number() -> None:
    config = {
        "tables": [
            {
                "example_rows": [
                    {"folder": 3, "name": "X", "description": "Desc for three"},
                ],
            },
        ],
    }
    assert (
        mod.get_example_description("03_cluster_with_analytics_nodes", config) == "Desc for three"
    )


def test_get_example_description_by_folder_name() -> None:
    config = {
        "tables": [
            {
                "example_rows": [
                    {
                        "folder_name": "custom_example",
                        "name": "X",
                        "description": "Custom desc",
                    },
                ],
            },
        ],
    }
    assert mod.get_example_description("custom_example", config) == "Custom desc"


def test_get_example_description_folder_name_case_insensitive() -> None:
    config = {
        "tables": [
            {
                "example_rows": [
                    {
                        "folder_name": "My_Example",
                        "name": "X",
                        "description": "Found",
                    },
                ],
            },
        ],
    }
    assert mod.get_example_description("my_example", config) == "Found"


def test_get_example_description_missing_returns_empty() -> None:
    assert mod.get_example_description("99_unknown", {}) == ""


def test_get_example_description_first_match_wins() -> None:
    config = {
        "tables": [
            {
                "example_rows": [
                    {"folder": 1, "name": "A", "description": "First"},
                ],
            },
            {
                "example_rows": [
                    {"folder": 1, "name": "B", "description": "Second"},
                ],
            },
        ],
    }
    assert mod.get_example_description("01_basic", config) == "First"
