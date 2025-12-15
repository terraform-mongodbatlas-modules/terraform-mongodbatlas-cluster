from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

from tf_gen.config import GenerationTarget, load_config


def test_load_config_minimal():
    config_yaml = """
providers:
  - provider_name: mongodbatlas
    provider_source: mongodb/mongodbatlas
    provider_version: "~> 2.1"
    resources:
      project:
        - output_dir: ./code/project
"""
    with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_yaml)
        f.flush()
        configs = load_config(Path(f.name))

    assert len(configs) == 1
    cfg = configs[0]
    assert cfg.provider_name == "mongodbatlas"
    assert cfg.provider_source == "mongodb/mongodbatlas"
    assert "project" in cfg.resources
    target = cfg.resources["project"][0]
    assert target.resource_type == "project"
    assert target.label == "this"
    assert not target.use_single_variable


def test_load_config_with_overrides():
    config_yaml = """
providers:
  - provider_name: mongodbatlas
    provider_source: mongodb/mongodbatlas
    resources:
      cloud_backup_schedule:
        - output_dir: ./code/cluster/modules/backup
          use_single_variable: true
          variables_excluded:
            - id
          variables_required:
            - cluster_name
            - project_id
"""
    with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_yaml)
        f.flush()
        configs = load_config(Path(f.name))

    target = configs[0].resources["cloud_backup_schedule"][0]
    assert target.use_single_variable
    assert "id" in target.variables_excluded
    assert "cluster_name" in target.variables_required


def test_generation_target_defaults():
    target = GenerationTarget()
    assert target.label == "this"
    assert target.resource_filename == "main.tf"
    assert target.variable_filename == "variables_resource.tf"
    assert target.output_filename == "output.tf"
    assert "variable" in target.files
    assert "resource" in target.files
    assert "output" in target.files
    assert not target.use_single_variable
    assert target.use_schema_computability
    assert not target.use_resource_count
    assert not target.include_id_field
