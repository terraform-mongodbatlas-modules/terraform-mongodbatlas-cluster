from __future__ import annotations

from pathlib import Path
from typing import Literal

import pytest
from tf_gen.config import GenerationTarget
from tf_gen.generators.outputs_tf import generate_outputs_tf
from tf_gen.generators.variables_tf import generate_variables_tf
from tf_gen.schema.models import parse_resource_schema

REGRESSIONS_DIR = Path(__file__).parent / "testdata" / "regressions"

# Schema configurations: (resource_name, schema_file, provider_name, test_types)
# test_types is a list of which generators to test: "variables", "outputs", or both
SCHEMA_CONFIGS: list[tuple[str, str, str, list[str]]] = [
    ("project", "project.json", "mongodbatlas", ["variables", "outputs"]),
    (
        "cloud_backup_schedule",
        "mongodbatlas_cloud_backup_schedule.json",
        "mongodbatlas",
        ["variables", "outputs"],
    ),
    (
        "advanced_cluster",
        "mongodbatlas_advanced_cluster.json",
        "mongodbatlas",
        ["variables", "outputs"],
    ),
    ("database_user", "mongodbatlas_database_user.json", "mongodbatlas", ["variables"]),
    ("vpc_endpoint", "vpc_endpoint.json", "aws", ["variables"]),
    (
        "advanced_cluster_v2",
        "mongodbatlas_advanced_clusterv2.json",
        "mongodbatlas",
        ["variables"],
    ),
]


def _generate_regression_cases():
    """Generate test cases as (resource_name, schema_file, provider_name, test_type)."""
    for resource_name, schema_file, provider_name, test_types in SCHEMA_CONFIGS:
        for test_type in test_types:
            yield pytest.param(
                resource_name,
                schema_file,
                provider_name,
                test_type,
                id=f"{resource_name}-{test_type}",
            )


@pytest.mark.parametrize(
    "resource_name,schema_file,provider_name,test_type",
    list(_generate_regression_cases()),
)
def test_schema_regression(
    resource_name: str,
    schema_file: str,
    provider_name: str,
    test_type: Literal["variables", "outputs"],
    load_schema,
    file_regression,
):
    """Unified regression test for both variables.tf and outputs.tf generation."""
    schema = load_schema(schema_file)
    parsed = parse_resource_schema(schema)
    config = GenerationTarget(resource_type=resource_name)

    if test_type == "variables":
        content = generate_variables_tf(parsed, config, provider_name)
        output_file = "variables.tf"
    else:
        content = generate_outputs_tf(parsed, config, provider_name)
        output_file = "outputs.tf"

    file_regression.check(
        content,
        fullpath=REGRESSIONS_DIR / resource_name / output_file,
    )
