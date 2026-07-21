from __future__ import annotations

import json
import logging
import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from shared import tf_retry
from tf_gen.schema.models import ResourceSchema, parse_resource_schema

logger = logging.getLogger(__name__)


def _make_cache_key(provider_source: str) -> str:
    """Generate cache key from provider source (e.g., 'mongodb/mongodbatlas' -> 'mongodbatlas')."""
    return provider_source.split("/")[-1]


def _run_terraform(args: list[str], cwd: Path, context: str) -> subprocess.CompletedProcess:
    """Run terraform command with proper error handling."""
    try:
        return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)
    except FileNotFoundError as e:
        msg = "terraform CLI not found. Install terraform to fetch provider schemas."
        raise RuntimeError(msg) from e
    except subprocess.CalledProcessError as e:
        stderr = e.stderr or ""
        stdout = e.stdout or ""
        msg = f"{context} failed (exit {e.returncode}):\nstderr: {stderr}\nstdout: {stdout}"
        raise RuntimeError(msg) from e


def fetch_provider_schema(
    provider_source: str,
    provider_version: str,
    cache_dir: Path | None = None,
) -> dict:
    if not provider_source:
        raise ValueError("provider_source is required (e.g., 'mongodb/mongodbatlas')")
    if not provider_version:
        raise ValueError(f"provider_version is required for {provider_source} (e.g., '1.0.0')")

    if tf_cli_config := os.environ.get("TF_CLI_CONFIG_FILE"):
        tf_cli_config_path = Path(tf_cli_config)
        content = tf_cli_config_path.read_text() if tf_cli_config_path.exists() else None
        logger.warning(
            f"TF_CLI_CONFIG_FILE={tf_cli_config} is set; provider schema may come from local build: {content}"  # noqa: E501
        )
    cache_key = _make_cache_key(provider_source)
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
        try:
            tf_retry.run_terraform_init(["terraform", "init"], tmp_path)
        except tf_retry.TerraformInitError as e:
            stderr = (e.stderr or "")[:200]
            msg = f"terraform init for {provider_source}@{provider_version} failed: {stderr}"
            raise RuntimeError(msg) from e
        result = _run_terraform(
            ["terraform", "providers", "schema", "-json"],
            cwd=tmp_path,
            context=f"terraform providers schema for {provider_source}@{provider_version}",
        )
        schema = json.loads(result.stdout)

    if cache_dir:
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f"{cache_key}.json"
        cache_file.write_text(json.dumps(schema, indent=2))

    return schema


def _find_provider_key(full_schema: dict, provider_name: str) -> str:
    for key in full_schema.get("provider_schemas", {}):
        if key.endswith(provider_name):
            return key
    raise ValueError(f"Provider {provider_name} not found in schema")


def list_resource_types(full_schema: dict, provider_name: str) -> list[str]:
    provider_key = _find_provider_key(full_schema, provider_name)
    resources = full_schema["provider_schemas"][provider_key].get("resource_schemas", {})
    prefix = f"{provider_name}_"
    return [k.removeprefix(prefix) for k in sorted(resources.keys())]


def extract_resource_schema(
    full_schema: dict, provider_name: str, resource_type: str
) -> ResourceSchema:
    provider_key = _find_provider_key(full_schema, provider_name)
    resources = full_schema["provider_schemas"][provider_key].get("resource_schemas", {})
    full_resource_type = f"{provider_name}_{resource_type}"
    if full_resource_type not in resources:
        raise ValueError(f"Resource {full_resource_type} not found")

    return parse_resource_schema(resources[full_resource_type])
