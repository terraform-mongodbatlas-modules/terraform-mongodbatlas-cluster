from __future__ import annotations

from pathlib import Path

import pytest

from workspace import models


def test_sanitize_address():
    assert models.sanitize_address("module.cluster.this") == "module_cluster_this"
    assert models.sanitize_address("resource.name") == "resource_name"
    assert models.sanitize_address('resource["203.0.113.0/24"]') == 'resource["203_0_113_0_24"]'


def test_ws_var_defaults():
    var = models.WsVar(name="test")
    assert var.expose_in_workspace
    assert var.module_value == ""
    assert var.var_type == ""


def test_example_path_found(tmp_path: Path):
    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()
    (examples_dir / "01_basic").mkdir()
    (examples_dir / "02_advanced").mkdir()
    ex = models.Example(number=1)
    assert ex.example_path(examples_dir).name == "01_basic"
    ex2 = models.Example(number=2)
    assert ex2.example_path(examples_dir).name == "02_advanced"


def test_example_path_not_found(tmp_path: Path):
    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()
    ex = models.Example(number=99)
    with pytest.raises(ValueError, match="Example 99_\\* not found"):
        ex.example_path(examples_dir)


def test_title_from_dir(tmp_path: Path):
    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()
    (examples_dir / "01_basic_cluster").mkdir()
    ex = models.Example(number=1)
    assert ex.title_from_dir(examples_dir) == "Basic Cluster"


def test_example_name_path_found(tmp_path: Path):
    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()
    (examples_dir / "backup_export").mkdir()
    ex = models.Example(name="backup_export")
    assert ex.example_path(examples_dir).name == "backup_export"
    assert ex.identifier == "backup_export"
    assert ex.title_from_dir(examples_dir) == "Backup Export"


def test_example_name_path_not_found(tmp_path: Path):
    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()
    ex = models.Example(name="missing")
    with pytest.raises(ValueError, match="Example 'missing' not found"):
        ex.example_path(examples_dir)


def test_example_identifier_number():
    ex = models.Example(number=5)
    assert ex.identifier == "05"


def test_example_identifier_name():
    ex = models.Example(name="encryption")
    assert ex.identifier == "encryption"


def test_example_identifier_missing():
    ex = models.Example()
    with pytest.raises(ValueError, match="must have either name or number"):
        _ = ex.identifier


def test_ws_config_exposed_vars():
    config = models.WsConfig(
        examples=[],
        var_groups={
            "shared": [
                models.WsVar(name="tags", expose_in_workspace=True),
                models.WsVar(name="project_id", expose_in_workspace=False),
            ],
            "group1": [models.WsVar(name="region", expose_in_workspace=True)],
        },
    )
    exposed = config.exposed_vars()
    names = [v.name for v in exposed]
    assert "tags" in names
    assert "region" in names
    assert "project_id" not in names


def test_ws_config_exposed_vars_deduplicates():
    config = models.WsConfig(
        examples=[],
        var_groups={
            "group1": [models.WsVar(name="tags", expose_in_workspace=True)],
            "group2": [models.WsVar(name="tags", expose_in_workspace=True)],
        },
    )
    exposed = config.exposed_vars()
    assert len(exposed) == 1
    assert exposed[0].name == "tags"


def test_ws_config_vars_for_example():
    config = models.WsConfig(
        examples=[],
        var_groups={
            "shared": [models.WsVar(name="tags")],
            "group1": [models.WsVar(name="project_id")],
        },
    )
    ex = models.Example(number=1, var_groups=["shared", "group1"])
    vars_list = config.vars_for_example(ex)
    names = [v.name for v in vars_list]
    assert names == ["tags", "project_id"]


def test_ws_config_vars_for_example_duplicate_raises():
    config = models.WsConfig(
        examples=[],
        var_groups={
            "shared": [models.WsVar(name="project_id")],
            "group1": [models.WsVar(name="project_id")],
        },
    )
    ex = models.Example(number=1, var_groups=["shared", "group1"])
    with pytest.raises(ValueError, match="Duplicate variable 'project_id' in example 01"):
        config.vars_for_example(ex)


def test_parse_ws_config(tmp_path: Path):
    ws_config = tmp_path / models.WORKSPACE_CONFIG_FILE
    ws_config.write_text("""
examples:
  - number: 1
    var_groups: [shared]
    plan_regressions:
      - address: module.cluster.this

var_groups:
  shared:
    - name: tags
      expose_in_workspace: true
      var_type: map(string)
      module_value: "{}"
""")
    config = models.parse_ws_config(ws_config)
    assert len(config.examples) == 1
    assert config.examples[0].number == 1
    assert config.examples[0].var_groups == ["shared"]
    assert len(config.examples[0].plan_regressions) == 1
    assert config.examples[0].plan_regressions[0].address == "module.cluster.this"
    assert "shared" in config.var_groups
    assert config.var_groups["shared"][0].name == "tags"


def test_parse_ws_config_named_example(tmp_path: Path):
    ws_config = tmp_path / models.WORKSPACE_CONFIG_FILE
    ws_config.write_text("""
examples:
  - name: backup_export
    var_groups: [shared]
    plan_regressions:
      - address: module.atlas_azure.mongodbatlas_cloud_provider_access_setup.this[0]

var_groups:
  shared:
    - name: project_id
      expose_in_workspace: false
      module_value: local.project_id
""")
    config = models.parse_ws_config(ws_config)
    assert len(config.examples) == 1
    assert config.examples[0].name == "backup_export"
    assert config.examples[0].number is None
    assert config.examples[0].identifier == "backup_export"


def test_parse_ws_config_output_assertions(tmp_path: Path):
    ws_config = tmp_path / models.WORKSPACE_CONFIG_FILE
    ws_config.write_text("""
examples:
  - name: backup_export
    var_groups: [shared]
    output_assertions:
      - output: export_bucket_id
        pattern: "^[a-f0-9]{24}$"
      - output: cluster_name
        not_empty: true

var_groups:
  shared:
    - name: project_id
      expose_in_workspace: false
      module_value: local.project_id
""")
    config = models.parse_ws_config(ws_config)
    assert len(config.examples[0].output_assertions) == 2
    a0 = config.examples[0].output_assertions[0]
    assert a0.output == "export_bucket_id"
    assert a0.pattern == "^[a-f0-9]{24}$"
    assert not a0.not_empty
    a1 = config.examples[0].output_assertions[1]
    assert a1.output == "cluster_name"
    assert a1.not_empty


def test_resolve_workspaces_all(tmp_path: Path):
    (tmp_path / "workspace_one").mkdir()
    (tmp_path / "workspace_two").mkdir()
    (tmp_path / "other_dir").mkdir()
    ws_dirs = models.resolve_workspaces("all", tmp_path)
    names = [d.name for d in ws_dirs]
    assert names == ["workspace_one", "workspace_two"]


def test_resolve_workspaces_specific(tmp_path: Path):
    ws_dir = tmp_path / "workspace_test"
    ws_dir.mkdir()
    (ws_dir / models.WORKSPACE_CONFIG_FILE).write_text("examples: []")
    ws_dirs = models.resolve_workspaces("workspace_test", tmp_path)
    assert len(ws_dirs) == 1
    assert ws_dirs[0].name == "workspace_test"


def test_resolve_workspaces_specific_missing_config(tmp_path: Path):
    ws_dir = tmp_path / "workspace_test"
    ws_dir.mkdir()
    with pytest.raises(ValueError, match=models.WORKSPACE_CONFIG_FILE):
        models.resolve_workspaces("workspace_test", tmp_path)


def test_resolve_workspaces_tests_dir_not_found(tmp_path: Path):
    missing = tmp_path / "missing"
    with pytest.raises(ValueError, match="does not exist"):
        models.resolve_workspaces("all", missing)


def test_resolve_workspaces_no_workspace_dirs(tmp_path: Path):
    with pytest.raises(ValueError, match="No workspace_\\* directories found"):
        models.resolve_workspaces("all", tmp_path)
