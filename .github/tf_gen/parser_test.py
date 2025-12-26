from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from tf_gen.schema.parser import (
    extract_resource_schema,
    fetch_provider_schema,
    list_resource_types,
)
from tf_gen.schema_config import (
    PROVIDER_VERSIONS,
    resources_by_provider,
)

MONGODBATLAS_SOURCE = os.getenv("MONGODBATLAS_SOURCE", "mongodb/mongodbatlas")
MONGODBATLAS_VERSION = os.getenv("MONGODBATLAS_VERSION", "~> 2.2")
TESTDATA_DIR = Path(__file__).parent / "testdata"
SCHEMAS_DIR = TESTDATA_DIR / "schemas"


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


def _find_provider_key(full_schema: dict, provider_name: str) -> str:
    """Find the provider key in the schema matching the provider name."""
    for key in full_schema.get("provider_schemas", {}):
        if key.endswith(provider_name):
            return key
    raise ValueError(f"Provider {provider_name} not found in schema")


def _extract_raw_resource_schema(
    full_schema: dict, provider_name: str, resource_type: str
) -> dict:
    """Extract raw resource schema dict (not parsed) for dumping to file."""
    provider_key = _find_provider_key(full_schema, provider_name)
    resources = full_schema["provider_schemas"][provider_key].get(
        "resource_schemas", {}
    )
    full_resource_type = f"{provider_name}_{resource_type}"
    if full_resource_type not in resources:
        raise ValueError(f"Resource {full_resource_type} not found")
    return resources[full_resource_type]


@pytest.mark.skipif(
    os.getenv("DOWNLOAD_SCHEMAS") != "1",
    reason="Set DOWNLOAD_SCHEMAS=1 to download schemas",
)
def test_schema_download(tmp_path_factory: pytest.TempPathFactory):
    """Download schemas for all active resources and save to testdata/schemas/.

    Run with: DOWNLOAD_SCHEMAS=1 pytest -k test_schema_download -v
    """
    cache_dir = tmp_path_factory.mktemp("provider_cache")
    SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)

    by_provider = resources_by_provider()
    downloaded = []
    errors = []

    for provider_source, resources in by_provider.items():
        version = PROVIDER_VERSIONS.get(provider_source)
        if not version:
            errors.append(f"No version configured for {provider_source}")
            continue

        # Fetch provider schema once per provider
        try:
            full_schema = fetch_provider_schema(provider_source, version, cache_dir)
        except Exception as e:
            errors.append(f"Failed to fetch {provider_source}: {e}")
            continue

        # Extract and save each resource
        for rc in resources:
            try:
                raw_schema = _extract_raw_resource_schema(
                    full_schema, rc.provider_name, rc.resource_type
                )
                output_path = SCHEMAS_DIR / rc.schema_filename
                output_path.write_text(json.dumps(raw_schema, indent=4))
                downloaded.append(rc.schema_filename)
            except Exception as e:
                errors.append(f"Failed to extract {rc.full_resource_type}: {e}")

    assert not errors, f"Errors: {errors}"
    assert downloaded, "No schemas were downloaded"
    print(f"\nDownloaded {len(downloaded)} schemas to {SCHEMAS_DIR}")
    for name in downloaded:
        print(f"  - {name}")
