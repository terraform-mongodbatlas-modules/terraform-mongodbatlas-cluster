from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class GenerationTarget(BaseModel):
    resource_type: str = ""
    output_dir: Path = Field(default_factory=Path.cwd)
    use_single_variable: bool = False
    use_schema_computability: bool = True
    use_resource_count: bool = False
    include_id_field: bool = False
    files: list[str] = Field(default_factory=lambda: ["variable", "resource", "output"])
    label: str = "this"
    resource_filename: str = "main.tf"
    resource_tf: dict[str, str] = Field(default_factory=dict)
    resource_tf_var_overrides: dict[str, str] = Field(default_factory=dict)
    variable_filename: str = "variables_resource.tf"
    variables_prefix: str = ""
    variables_excluded: list[str] = Field(default_factory=list)
    variables_required: list[str] = Field(default_factory=list)
    variable_tf: dict[str, dict[str, Any]] = Field(default_factory=dict)
    output_filename: str = "output.tf"
    outputs_excluded: list[str] = Field(default_factory=list)
    output_tf_overrides: dict[str, dict[str, Any]] = Field(default_factory=dict)


class ProviderGenConfig(BaseModel):
    provider_name: str
    provider_source: str
    provider_version: str = "~> 1.0"
    provider_config_block: str = ""
    resources: dict[str, list[GenerationTarget]] = Field(default_factory=dict)


def load_config(path: Path) -> list[ProviderGenConfig]:
    raw = yaml.safe_load(path.read_text())
    providers = raw.get("providers", [])
    result = []
    for p in providers:
        resources: dict[str, list[GenerationTarget]] = {}
        for resource_type, targets in p.get("resources", {}).items():
            if isinstance(targets, list):
                resources[resource_type] = [
                    GenerationTarget(resource_type=resource_type, **t) for t in targets
                ]
            else:
                resources[resource_type] = [
                    GenerationTarget(resource_type=resource_type, **targets)
                ]
        result.append(
            ProviderGenConfig(
                provider_name=p.get("provider_name", ""),
                provider_source=p.get("provider_source", ""),
                provider_version=p.get("provider_version", "~> 1.0"),
                provider_config_block=p.get("provider_config_block", ""),
                resources=resources,
            )
        )
    return result
