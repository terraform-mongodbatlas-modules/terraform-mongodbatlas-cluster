from __future__ import annotations

import json
from pathlib import Path

import pytest

TESTDATA_DIR = Path(__file__).parent / "testdata"
SCHEMAS_DIR = TESTDATA_DIR / "schemas"


@pytest.fixture(scope="session")
def testdata_dir() -> Path:
    return TESTDATA_DIR


@pytest.fixture(scope="session")
def schema_cache() -> dict[str, dict]:
    """Session-scoped cache for loaded schemas to avoid re-reading files."""
    return {}


@pytest.fixture(scope="session")
def load_schema(schema_cache: dict[str, dict]):
    """Factory fixture to load schemas with caching.

    Accepts either:
    - filename in testdata/ (e.g., "project.json")
    - path relative to testdata/ (e.g., "schemas/mongodbatlas_project.json")
    """

    def _load(filename: str) -> dict:
        if filename not in schema_cache:
            # Check schemas/ subdirectory first, then testdata root
            schema_path = SCHEMAS_DIR / filename
            if not schema_path.exists():
                schema_path = TESTDATA_DIR / filename
            if not schema_path.exists():
                raise FileNotFoundError(f"Schema not found: {filename}")
            schema_cache[filename] = json.loads(schema_path.read_text())
        return schema_cache[filename]

    return _load


# Individual schema fixtures for backward compatibility and direct usage
@pytest.fixture(scope="module")
def backup_schedule_schema(load_schema) -> dict:
    return load_schema("mongodbatlas_cloud_backup_schedule.json")


@pytest.fixture(scope="module")
def vpc_endpoint_schema(load_schema) -> dict:
    return load_schema("vpc_endpoint.json")


@pytest.fixture(scope="module")
def advanced_cluster_schema(load_schema) -> dict:
    return load_schema("mongodbatlas_advanced_cluster.json")


@pytest.fixture(scope="module")
def project_schema(load_schema) -> dict:
    return load_schema("project.json")


@pytest.fixture(scope="module")
def database_user_schema(load_schema) -> dict:
    return load_schema("mongodbatlas_database_user.json")


@pytest.fixture(scope="module")
def advanced_cluster_v2_schema(load_schema) -> dict:
    return load_schema("mongodbatlas_advanced_clusterv2.json")
