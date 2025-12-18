from __future__ import annotations

import json
from pathlib import Path

import pytest

TESTDATA_DIR = Path(__file__).parent / "testdata"
SCHEMAS_DIR = TESTDATA_DIR / "schemas"

# Default provider configurations for tests
# Test configs can reference these by provider_name without repeating source/version
# Version constraints use ~> X.0 to allow any minor version within major X (equivalent to "X.x")
DEFAULT_PROVIDERS = {
    "mongodbatlas": {
        "provider_name": "mongodbatlas",
        "provider_source": "mongodb/mongodbatlas",
        "provider_version": "~> 2.0",  # 2.x
    },
    "aws": {
        "provider_name": "aws",
        "provider_source": "hashicorp/aws",
        "provider_version": "~> 6.0",  # 6.x
    },
    "azurerm": {
        "provider_name": "azurerm",
        "provider_source": "hashicorp/azurerm",
        "provider_version": "~> 4.0",  # 4.x
    },
    "google": {
        "provider_name": "google",
        "provider_source": "hashicorp/google",
        "provider_version": "~> 7.0",  # 7.x
    },
}


@pytest.fixture(scope="session")
def testdata_dir() -> Path:
    return TESTDATA_DIR


@pytest.fixture(scope="session")
def schema_cache() -> dict[str, dict]:
    """Session-scoped cache for loaded schemas to avoid re-reading files."""
    return {}


@pytest.fixture(scope="session")
def load_schema(schema_cache: dict[str, dict]):
    """Factory fixture to load schemas from testdata/schemas/ with caching."""

    def _load(filename: str) -> dict:
        if filename not in schema_cache:
            schema_path = SCHEMAS_DIR / filename
            if not schema_path.exists():
                raise FileNotFoundError(f"Schema not found: {schema_path}")
            schema_cache[filename] = json.loads(schema_path.read_text())
        return schema_cache[filename]

    return _load


# Individual schema fixtures for backward compatibility and direct usage
@pytest.fixture(scope="module")
def backup_schedule_schema(load_schema) -> dict:
    return load_schema("mongodbatlas_cloud_backup_schedule.json")


@pytest.fixture(scope="module")
def vpc_endpoint_schema(load_schema) -> dict:
    return load_schema("aws_vpc_endpoint.json")


@pytest.fixture(scope="module")
def advanced_cluster_schema(load_schema) -> dict:
    return load_schema("mongodbatlas_advanced_cluster.json")


@pytest.fixture(scope="module")
def project_schema(load_schema) -> dict:
    return load_schema("mongodbatlas_project.json")


@pytest.fixture(scope="module")
def database_user_schema(load_schema) -> dict:
    return load_schema("mongodbatlas_database_user.json")


@pytest.fixture(scope="module")
def advanced_cluster_v2_schema(load_schema) -> dict:
    return load_schema("mongodbatlas_advanced_clusterv2.json")


@pytest.fixture
def cli_testdata_dir(testdata_dir: Path) -> Path:
    return testdata_dir / "cli"


@pytest.fixture
def cli_regression_dir(testdata_dir: Path) -> Path:
    return testdata_dir / "cli_regression"
