from __future__ import annotations

from pathlib import Path

import pytest
from tf_gen.config import GenerationTarget
from tf_gen.generators.outputs_tf import generate_outputs_tf
from tf_gen.generators.variables_tf import generate_variables_tf
from tf_gen.schema.models import parse_resource_schema

REGRESSIONS_DIR = Path(__file__).parent / "testdata" / "regressions"


def regression_path(resource_name: str, filename: str) -> Path:
    return REGRESSIONS_DIR / resource_name / filename


@pytest.fixture
def check_variables_regression(file_regression):
    def _check(schema: dict, resource_name: str, provider_name: str = "mongodbatlas"):
        parsed = parse_resource_schema(schema)
        config = GenerationTarget(resource_type=resource_name)
        content = generate_variables_tf(parsed, config, provider_name)
        file_regression.check(
            content,
            fullpath=regression_path(resource_name, "variables.tf"),
        )

    return _check


@pytest.fixture
def check_outputs_regression(file_regression):
    def _check(schema: dict, resource_name: str, provider_name: str = "mongodbatlas"):
        parsed = parse_resource_schema(schema)
        config = GenerationTarget(resource_type=resource_name)
        content = generate_outputs_tf(parsed, config, provider_name)
        file_regression.check(
            content,
            fullpath=regression_path(resource_name, "outputs.tf"),
        )

    return _check


def test_project_variables(check_variables_regression, project_schema: dict):
    check_variables_regression(project_schema, "project")


def test_backup_schedule_variables(
    check_variables_regression, backup_schedule_schema: dict
):
    check_variables_regression(backup_schedule_schema, "cloud_backup_schedule")


def test_advanced_cluster_variables(
    check_variables_regression, advanced_cluster_schema: dict
):
    check_variables_regression(advanced_cluster_schema, "advanced_cluster")


def test_database_user_variables(
    check_variables_regression, database_user_schema: dict
):
    check_variables_regression(database_user_schema, "database_user")


def test_vpc_endpoint_variables(check_variables_regression, vpc_endpoint_schema: dict):
    check_variables_regression(vpc_endpoint_schema, "vpc_endpoint", provider_name="aws")


def test_advanced_cluster_v2_variables(
    check_variables_regression, advanced_cluster_v2_schema: dict
):
    check_variables_regression(advanced_cluster_v2_schema, "advanced_cluster_v2")


def test_project_outputs(check_outputs_regression, project_schema: dict):
    check_outputs_regression(project_schema, "project")


def test_advanced_cluster_outputs(
    check_outputs_regression, advanced_cluster_schema: dict
):
    check_outputs_regression(advanced_cluster_schema, "advanced_cluster")


def test_cloud_backup_schedule_outputs(
    check_outputs_regression, backup_schedule_schema: dict
):
    check_outputs_regression(backup_schedule_schema, "cloud_backup_schedule")
