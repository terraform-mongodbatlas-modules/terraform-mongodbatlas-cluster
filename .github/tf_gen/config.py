from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Self

import yaml
from pydantic import BaseModel, Field, model_validator


class FileType(StrEnum):
    variable = "variable"
    resource = "resource"
    output = "output"


class VariableAttributeOverride(BaseModel):
    name: str | None = None
    description: str | None = None
    default: str | None = None
    type: str | None = None
    sensitive: bool | None = None
    validation: str | None = None


class OutputAttributeOverride(BaseModel):
    name: str | None = None
    value: str | None = None
    include_children: bool | None = None
    sensitive: bool | None = None


class ResourceMetaArgs(BaseModel):
    count: str | None = None
    provider: str | None = None
    depends_on: list[str] = Field(default_factory=list)
    lifecycle: str | None = None


class GenerationTarget(BaseModel):
    resource_type: str = ""
    output_dir: Path = Field(default_factory=Path.cwd)
    use_single_variable: bool = False
    use_single_output: bool = False
    all_variables_optional: bool = False
    use_resource_count: bool = False
    include_id_field: bool = False
    files: list[FileType] = Field(default_factory=lambda: list(FileType))
    label: str = "this"
    resource_filename: str = "main.tf"
    resource_tf: ResourceMetaArgs = Field(default_factory=ResourceMetaArgs)
    resource_tf_var_overrides: dict[str, str] = Field(default_factory=dict)
    variable_filename: str = "variables_resource.tf"
    variables_prefix: str = ""
    variables_excluded: list[str] = Field(default_factory=list)
    variables_required: list[str] = Field(default_factory=list)
    variable_tf: dict[str, VariableAttributeOverride] = Field(default_factory=dict)
    output_filename: str = "outputs.tf"
    outputs_prefix: str = ""
    outputs_excluded: list[str] = Field(default_factory=list)
    output_tf_overrides: dict[str, OutputAttributeOverride] = Field(
        default_factory=dict
    )
    output_attribute_max_children: int = 5

    @model_validator(mode="after")
    def validate_single_output_no_overrides(self) -> Self:
        if self.use_single_output and self.output_tf_overrides:
            msg = "output_tf_overrides cannot be used with use_single_output=True"
            raise ValueError(msg)
        return self


class ProviderGenConfig(BaseModel):
    provider_name: str
    provider_source: str
    provider_version: str = "~> 1.0"
    provider_config_block: str = ""
    resources: dict[str, list[GenerationTarget]] = Field(default_factory=dict)


def load_config(
    path: Path, provider_defaults: dict[str, dict[str, str]] | None = None
) -> list[ProviderGenConfig]:
    raw = yaml.safe_load(path.read_text())
    providers = raw.get("providers", [])
    result = []
    for p in providers:
        provider_name = p.get("provider_name", "")
        defaults = (provider_defaults or {}).get(provider_name, {})
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
                provider_name=provider_name,
                provider_source=p.get("provider_source")
                or defaults.get("provider_source", ""),
                provider_version=p.get("provider_version")
                or defaults.get("provider_version", "~> 1.0"),
                provider_config_block=p.get("provider_config_block", ""),
                resources=resources,
            )
        )
    return result
