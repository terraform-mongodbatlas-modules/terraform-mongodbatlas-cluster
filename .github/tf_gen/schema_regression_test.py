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


TestType = Literal["variables", "outputs", "main"]


def _generate_cases(test_types: list[TestType]):
    """Generate test cases from ACTIVE_RESOURCES config for given test types."""
    for rc in ACTIVE_RESOURCES:
        for test_type in test_types:
            yield pytest.param(rc, test_type, id=f"{rc.resource_type}-{test_type}")


@pytest.mark.parametrize("rc,test_type", list(_generate_cases(["variables", "outputs", "main"])))
def test_schema_regression(
    rc: ResourceConfig,
    test_type: TestType,
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


@pytest.mark.parametrize("rc,test_type", list(_generate_cases(["variables", "main", "outputs"])))
def test_schema_regression_single_variable(
    rc: ResourceConfig,
    test_type: TestType,
    load_schema,
    file_regression,
):
    """Regression test for single_variable mode (variables.tf, main.tf, and outputs.tf)."""
    schema = load_schema(rc.schema_filename)
    parsed = parse_resource_schema(schema)
    config = GenerationTarget(
        resource_type=rc.resource_type,
        use_single_variable=True,
        use_single_output=True,
    )

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
        fullpath=REGRESSIONS_DIR / f"{rc.resource_type}_single" / output_file,
    )


@pytest.mark.parametrize("rc", ACTIVE_RESOURCES, ids=lambda rc: rc.resource_type)
def test_schema_regression_count(
    rc: ResourceConfig,
    load_schema,
    file_regression,
):
    """Regression test for use_resource_count mode (outputs.tf only)."""
    schema = load_schema(rc.schema_filename)
    parsed = parse_resource_schema(schema)
    config = GenerationTarget(resource_type=rc.resource_type, use_resource_count=True)
    content = generate_outputs_tf(parsed, config, rc.provider_name)

    file_regression.check(
        content,
        fullpath=REGRESSIONS_DIR / f"{rc.resource_type}_count" / "outputs.tf",
    )
