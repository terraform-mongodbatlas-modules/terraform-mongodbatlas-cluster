from __future__ import annotations

import textwrap

import generate_inputs_from_readme as mod
import pytest


def _dedent(s: str) -> str:
    return textwrap.dedent(s).lstrip("\n").rstrip() + "\n"


def test_parse_terraform_docs_inputs_required_and_optional_with_scalars() -> None:
    inputs_block = _dedent(
        """
        ## Required Inputs

        The following input variables are required:

        ### <a name="input_project_id"></a> [project_id](#input_project_id)

        Description: Unique 24-hexadecimal digit string that identifies your project.

        Type: `string`

        ## Optional Inputs

        The following input variables are optional (have default values):

        ### <a name="input_backup_enabled"></a> [backup_enabled](#input_backup_enabled)

        Description: Recommended for production clusters. Flag that indicates whether the cluster can perform backups.

        Type: `bool`
        Default: `true`
        """
    )

    variables = mod.parse_terraform_docs_inputs(inputs_block)

    # We expect two variables parsed with correct required flags and scalar types/defaults.
    by_name = {v.name: v for v in variables}
    assert set(by_name) == {"project_id", "backup_enabled"}

    project = by_name["project_id"]
    assert project.required
    assert "Unique 24-hexadecimal digit string" in project.description
    assert project.type == "`string`"
    assert project.default == ""

    backup = by_name["backup_enabled"]
    assert not backup.required
    assert "Recommended for production clusters" in backup.description
    assert backup.type == "`bool`"
    assert backup.default == "`true`"


def test_parse_terraform_docs_inputs_preserves_fenced_type_and_default() -> None:
    inputs_block = _dedent(
        """
        ## Optional Inputs

        ### <a name="input_regions"></a> [regions](#input_regions)

        Description: The simplest way to define your cluster topology:
        - Set `name`, for example `US_EAST_1`.

        Type:

        ```hcl
        list(object({
          name  = string
          nodes = optional(number)
        }))
        ```

        Default:

        ```hcl
        []
        ```
        """
    )

    variables = mod.parse_terraform_docs_inputs(inputs_block)
    assert len(variables) == 1
    regions = variables[0]

    # Description should preserve bullet line breaks (we keep them as-is, minus trailing whitespace).
    assert "The simplest way to define your cluster topology:" in regions.description
    assert "- Set `name`, for example `US_EAST_1`." in regions.description

    # Type should contain the full fenced block, not a flattened one-liner.
    assert regions.type.startswith("```hcl")
    assert "list(object({" in regions.type
    assert regions.type.strip().endswith("```")

    # Default should also be preserved as a fenced block.
    assert regions.default.startswith("```hcl")
    assert "[]" in regions.default
    assert regions.default.strip().endswith("```")


def test_parse_terraform_docs_inputs_raises_on_empty_block() -> None:
    empty_block = (
        "## Required Inputs\n\nThe following input variables are required:\n\n"
    )

    with pytest.raises(SystemExit) as exc_info:
        mod.parse_terraform_docs_inputs(empty_block)

    assert "No variables were parsed" in str(exc_info.value)


def test_render_grouped_markdown_with_section_description() -> None:
    """Test that section descriptions from YAML config are rendered correctly."""
    variables = [
        mod.Variable(
            name="test_var",
            description="A test variable",
            type="`string`",
            default="`null`",
            required=False,
        )
    ]

    sections = [
        {
            "id": "test_section",
            "title": "Test Section",
            "level": 2,
            "description": "This is a section description.\nIt can span multiple lines.",
            "match": {"names": ["test_var"]},
        }
    ]

    output = mod.render_grouped_markdown(variables, sections)

    assert "## Test Section" in output
    assert "This is a section description." in output
    assert "It can span multiple lines." in output
    assert "### test_var" in output
    # Description should appear before variables
    assert output.find("This is a section description") < output.find("### test_var")
