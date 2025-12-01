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


_indented_hcl_content = """\
```hcl
list(object({
    name                    = string
    disk_iops               = optional(number)
    disk_size_gb            = optional(number)
    ebs_volume_type         = optional(string)
    instance_size           = optional(string)
    instance_size_analytics = optional(string)
    node_count              = optional(number)
    node_count_analytics    = optional(number)
    node_count_read_only    = optional(number)
    provider_name           = optional(string)
    shard_number            = optional(number)
    zone_name               = optional(string)
  }))
```"""
_wanted_hcl_content = """\
```hcl
list(object({
  name                    = string
  disk_iops               = optional(number)
  disk_size_gb            = optional(number)
  ebs_volume_type         = optional(string)
  instance_size           = optional(string)
  instance_size_analytics = optional(string)
  node_count              = optional(number)
  node_count_analytics    = optional(number)
  node_count_read_only    = optional(number)
  provider_name           = optional(string)
  shard_number            = optional(number)
  zone_name               = optional(string)
}))
```"""


def test_removing_indent():
    assert mod.avoid_extra_type_indent(_indented_hcl_content) == _wanted_hcl_content
    assert mod.avoid_extra_type_indent("string") == "string"  # no change


_expected_preserved_lines = """\
- See [auto_scaling](#auto-scaling) vs [manual scaling](#manual-scaling) below.

**NOTE**:

- The order"""


def test_preserving_blank_lines_in_description() -> None:
    description = """\
### <a name="input_regions"></a> [regions](#input\_regions)

Description: The simplest way to define your cluster topology:
- Set `name`, for example `US_EAST_1`, see all valid [region names](https://www.mongodb.com/docs/atlas/cloud-providers-regions/).
- Set `node_count`, `node_count_read_only`, `node_count_analytics` depending on your needs.
- Set `provider_name` (AWS/AZURE/GCP) or use the "root" level `provider_name` variable if all regions share the `provider_name`.
- For `cluster_type.REPLICASET`: omit both `shard_number` and `zone_name`.
- For `cluster_type.SHARDED`: set `shard_number` on each region or use the `shard_count` [variable](#shard\_count); do not set `zone_name`. Regions with the same `shard_number` belong to the same shard.
- For `cluster_type.GEOSHARDED`: set `zone_name` on each region; optionally set `shard_number`. Regions with the same `zone_name` form one zone.
- See [auto\_scaling](#auto-scaling) vs [manual scaling](#manual-scaling) below.

**NOTE**:

- The order in which region blocks are defined in this list determines their priority within each shard or zone.
  - The first region gets priority 7 (maximum), the next 6, and so on (minimum 0). For more context, see [this section of the Atlas Admin API documentation](https://www.mongodb.com/docs/api/doc/atlas-admin-api-v2/operation/operation-creategroupcluster#operation-creategroupcluster-body-application-vnd-atlas-2024-10-23-json-replicationspecs-regionconfigs-priority).
- Within a zone, `shard_numbers` are specific to that zone and independent of the `shard_number` in any other zones.
- The `shard_number` variable is specific to this module. It groups regions within a shard and does not represent an actual value in Atlas.

"""
    parsed = mod.parse_terraform_docs_inputs(description)
    assert _expected_preserved_lines in parsed[0].description
