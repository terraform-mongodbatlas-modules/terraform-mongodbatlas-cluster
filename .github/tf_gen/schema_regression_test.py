from __future__ import annotations

from pathlib import Path
from typing import Literal

import pytest
from tf_gen.config import GenerationTarget
from tf_gen.generators.main_tf import generate_main_tf
from tf_gen.generators.outputs_tf import generate_outputs_tf
from tf_gen.generators.variables_tf import generate_variables_tf
from tf_gen.schema.models import parse_resource_schema
from tf_gen.schema_config import ACTIVE_RESOURCES, ResourceConfig

REGRESSIONS_DIR = Path(__file__).parent / "testdata" / "regressions"


def _generate_regression_cases():
    """Generate test cases from ACTIVE_RESOURCES config."""
    for rc in ACTIVE_RESOURCES:
        for test_type in ("variables", "outputs", "main"):
            yield pytest.param(rc, test_type, id=f"{rc.resource_type}-{test_type}")


@pytest.mark.parametrize("rc,test_type", list(_generate_regression_cases()))
def test_schema_regression(
    rc: ResourceConfig,
    test_type: Literal["variables", "outputs", "main"],
    load_schema,
    file_regression,
):
    """Unified regression test for variables.tf, outputs.tf, and main.tf generation."""
    schema = load_schema(rc.schema_filename)
    parsed = parse_resource_schema(schema)
    config = GenerationTarget(resource_type=rc.resource_type)

    if test_type == "variables":
        content = generate_variables_tf(parsed, config, rc.provider_name)
        output_file = "variables.tf"
    elif test_type == "main":
        content = generate_main_tf(parsed, config, rc.provider_name)
        output_file = "main.tf"
    else:
        content = generate_outputs_tf(parsed, config, rc.provider_name)
        output_file = "outputs.tf"

    file_regression.check(
        content,
        fullpath=REGRESSIONS_DIR / rc.resource_type / output_file,
    )
