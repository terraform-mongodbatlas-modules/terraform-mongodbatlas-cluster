from __future__ import annotations

from pathlib import Path
from typing import Literal

import pytest
from tf_gen.config import GenerationTarget
from tf_gen.generators.outputs_tf import generate_outputs_tf
from tf_gen.generators.variables_tf import generate_variables_tf
from tf_gen.schema.models import parse_resource_schema
from tf_gen.schema_config import ACTIVE_RESOURCES, ResourceConfig

REGRESSIONS_DIR = Path(__file__).parent / "testdata" / "regressions"

# Legacy schema filename mappings for files that don't follow the standard naming
# Maps resource_type -> actual filename in testdata/
LEGACY_SCHEMA_FILES: dict[str, str] = {
    "project": "project.json",
    "vpc_endpoint": "vpc_endpoint.json",
}


def _get_schema_filename(rc: ResourceConfig) -> str:
    """Get schema filename, using legacy mapping if available."""
    return LEGACY_SCHEMA_FILES.get(rc.resource_type, rc.schema_filename)


def _generate_regression_cases():
    """Generate test cases from ACTIVE_RESOURCES config."""
    for rc in ACTIVE_RESOURCES:
        if rc.test_variables:
            yield pytest.param(rc, "variables", id=f"{rc.resource_type}-variables")
        if rc.test_outputs:
            yield pytest.param(rc, "outputs", id=f"{rc.resource_type}-outputs")


@pytest.mark.parametrize("rc,test_type", list(_generate_regression_cases()))
def test_schema_regression(
    rc: ResourceConfig,
    test_type: Literal["variables", "outputs"],
    load_schema,
    file_regression,
):
    """Unified regression test for both variables.tf and outputs.tf generation."""
    schema_filename = _get_schema_filename(rc)
    schema = load_schema(schema_filename)
    parsed = parse_resource_schema(schema)
    config = GenerationTarget(resource_type=rc.resource_type)

    if test_type == "variables":
        content = generate_variables_tf(parsed, config, rc.provider_name)
        output_file = "variables.tf"
    else:
        content = generate_outputs_tf(parsed, config, rc.provider_name)
        output_file = "outputs.tf"

    file_regression.check(
        content,
        fullpath=REGRESSIONS_DIR / rc.resource_type / output_file,
    )
