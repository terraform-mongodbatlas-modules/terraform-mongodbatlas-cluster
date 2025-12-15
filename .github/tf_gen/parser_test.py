from __future__ import annotations

import os
from pathlib import Path

import pytest
from tf_gen.schema.parser import (
    extract_resource_schema,
    fetch_provider_schema,
    list_resource_types,
)

MONGODBATLAS_SOURCE = os.getenv("MONGODBATLAS_SOURCE", "mongodb/mongodbatlas")
MONGODBATLAS_VERSION = os.getenv("MONGODBATLAS_VERSION", "~> 2.2")


@pytest.fixture(scope="module")
def schema_cache_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("schema_cache")


@pytest.fixture(scope="module")
def mongodbatlas_schema(schema_cache_dir: Path) -> dict:
    return fetch_provider_schema(
        MONGODBATLAS_SOURCE, MONGODBATLAS_VERSION, schema_cache_dir
    )


def test_fetch_and_list_resource_types(mongodbatlas_schema: dict):
    resource_types = list_resource_types(mongodbatlas_schema, "mongodbatlas")
    assert len(resource_types) > 50
    assert "project" in resource_types
    assert "advanced_cluster" in resource_types
    assert "cloud_backup_schedule" in resource_types


def test_parse_all_resource_schemas(mongodbatlas_schema: dict):
    resource_types = list_resource_types(mongodbatlas_schema, "mongodbatlas")
    errors = []
    for rt in resource_types:
        try:
            extract_resource_schema(mongodbatlas_schema, "mongodbatlas", rt)
        except Exception as e:
            errors.append(f"{rt}: {e}")
    assert not errors, f"Failed to parse: {errors}"
