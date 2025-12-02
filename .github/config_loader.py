"""Shared configuration loading and parsing for documentation generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class CodeSnippetFilesConfig:
    """Configuration for code snippet file extraction."""

    additional: list[str] = field(default_factory=list)


@dataclass
class TemplateVarsConfig:
    """Configuration for template variables."""

    skip_if_name_contains: list[str] = field(default_factory=list)
    vars: dict[str, str] = field(default_factory=dict)


@dataclass
class VersionsTfConfig:
    """Configuration for versions.tf generation."""

    add: str = ""
    skip_if_name_contains: list[str] = field(default_factory=list)
    generate_when_missing_only: bool = False
    force_generate: bool = False


@dataclass
class ExamplesReadmeConfig:
    """Configuration for example README generation."""

    readme_template: str
    skip_examples: list[str] = field(default_factory=list)
    code_snippet_files: CodeSnippetFilesConfig = field(
        default_factory=CodeSnippetFilesConfig
    )
    template_vars: TemplateVarsConfig = field(default_factory=TemplateVarsConfig)
    versions_tf: VersionsTfConfig = field(default_factory=VersionsTfConfig)


def load_examples_config(config_path: Path | None = None) -> dict:
    """Load the examples YAML configuration."""
    if config_path is None:
        root_dir = Path.cwd()
        config_path = root_dir / "docs" / "examples.yaml"

    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_examples_readme_config(config_dict: dict) -> ExamplesReadmeConfig:
    """Parse examples_readme configuration from YAML dict."""
    examples_readme_dict = config_dict.get("examples_readme", {})

    code_snippet_files_dict = examples_readme_dict.get("code_snippet_files", {})
    code_snippet_files = CodeSnippetFilesConfig(**code_snippet_files_dict)

    template_vars_dict = examples_readme_dict.get("template_vars", {})
    skip_if_name_contains = template_vars_dict.pop("skip_if_name_contains", [])
    template_vars = TemplateVarsConfig(
        skip_if_name_contains=skip_if_name_contains, vars=template_vars_dict
    )

    versions_tf_dict = examples_readme_dict.get("versions_tf", {})
    versions_tf = VersionsTfConfig(**versions_tf_dict)

    examples_readme_dict_filtered = {
        k: v
        for k, v in examples_readme_dict.items()
        if k not in ("code_snippet_files", "template_vars", "versions_tf")
    }
    return ExamplesReadmeConfig(
        **examples_readme_dict_filtered,
        code_snippet_files=code_snippet_files,
        template_vars=template_vars,
        versions_tf=versions_tf,
    )
