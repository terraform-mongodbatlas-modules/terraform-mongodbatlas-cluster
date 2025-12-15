from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from tf_gen.schema.models import ResourceSchema, parse_resource_schema

logger = logging.getLogger(__name__)


def fetch_provider_schema(
    provider_source: str,
    provider_version: str,
    cache_dir: Path | None = None,
) -> dict:
    cache_key = f"{provider_source.replace('/', '_')}_{provider_version}"
    if cache_dir:
        cache_file = cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            return json.loads(cache_file.read_text())

    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        versions_tf = tmp_path / "versions.tf"
        versions_tf.write_text(f'''
terraform {{
  required_providers {{
    provider = {{
      source  = "{provider_source}"
      version = "{provider_version}"
    }}
  }}
}}
''')
        subprocess.run(
            ["terraform", "init"], cwd=tmp_path, check=True, capture_output=True
        )
        result = subprocess.run(
            ["terraform", "providers", "schema", "-json"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
            text=True,
        )
        schema = json.loads(result.stdout)

    if cache_dir:
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f"{cache_key}.json"
        cache_file.write_text(json.dumps(schema, indent=2))

    return schema


def extract_resource_schema(
    full_schema: dict, provider_name: str, resource_type: str
) -> ResourceSchema:
    provider_key = None
    for key in full_schema.get("provider_schemas", {}):
        if key.endswith(provider_name):
            provider_key = key
            break
    if not provider_key:
        raise ValueError(f"Provider {provider_name} not found in schema")

    resources = full_schema["provider_schemas"][provider_key].get(
        "resource_schemas", {}
    )
    full_resource_type = f"{provider_name}_{resource_type}"
    if full_resource_type not in resources:
        raise ValueError(f"Resource {full_resource_type} not found")

    return parse_resource_schema(resources[full_resource_type])
