from __future__ import annotations

from tf_gen.config import GenerationTarget, ResourceMetaArgs
from tf_gen.generators.main_tf import (
    build_var_ref,
    generate_main_tf,
    render_block,
    should_include_in_resource,
)
from tf_gen.schema.models import (
    SchemaAttribute,
    SchemaBlock,
    SchemaBlockType,
    parse_resource_schema,
)
from tf_gen.schema.types import NestingMode


def test_should_include_excludes_computed_only():
    attr = SchemaAttribute(computed=True, optional=False, required=False)
    config = GenerationTarget()
    assert not should_include_in_resource("cluster_id", attr, config)


def test_should_include_excludes_id_by_default():
    attr = SchemaAttribute(computed=True, optional=True)
    config = GenerationTarget()
    assert not should_include_in_resource("id", attr, config)
    config_with_id = GenerationTarget(include_id_field=True)
    assert should_include_in_resource("id", attr, config_with_id)


def test_should_include_excludes_from_list():
    attr = SchemaAttribute(required=True)
    config = GenerationTarget(variables_excluded=["cluster_name"])
    assert not should_include_in_resource("cluster_name", attr, config)


def test_build_var_ref_simple():
    config = GenerationTarget(resource_type="project")
    assert build_var_ref("name", config, "mongodbatlas") == "var.name"


def test_build_var_ref_with_prefix():
    config = GenerationTarget(resource_type="project", variables_prefix="atlas_")
    assert build_var_ref("name", config, "mongodbatlas") == "var.atlas_name"


def test_build_var_ref_single_variable():
    config = GenerationTarget(resource_type="project", use_single_variable=True)
    assert build_var_ref("name", config, "mongodbatlas") == "var.mongodbatlas_project.name"


def test_build_var_ref_override():
    config = GenerationTarget(
        resource_type="project",
        resource_tf_var_overrides={"project_id": "local.project_id"},
    )
    assert build_var_ref("project_id", config, "mongodbatlas") == "local.project_id"


def test_render_optional_list_block():
    bt = SchemaBlockType(
        nesting_mode=NestingMode.list,
        block=SchemaBlock(
            attributes={
                "name": SchemaAttribute(required=True),
                "value": SchemaAttribute(required=True),
            }
        ),
    )
    config = GenerationTarget(resource_type="project")
    lines = render_block("limits", bt, config, "mongodbatlas")
    content = "\n".join(lines)
    assert 'dynamic "limits"' in content
    assert "for_each = var.limits == null ? [] : var.limits" in content
    assert "limits.value.name" in content


def test_render_optional_single_block():
    bt = SchemaBlockType(
        nesting_mode=NestingMode.single,
        max_items=1,
        block=SchemaBlock(attributes={"enabled": SchemaAttribute(optional=True)}),
    )
    config = GenerationTarget(resource_type="backup")
    lines = render_block("export", bt, config, "mongodbatlas")
    content = "\n".join(lines)
    assert 'dynamic "export"' in content
    assert "[var.export]" in content


def test_render_required_single_block():
    bt = SchemaBlockType(
        nesting_mode=NestingMode.single,
        min_items=1,
        block=SchemaBlock(attributes={"name": SchemaAttribute(required=True)}),
    )
    config = GenerationTarget(resource_type="test")
    lines = render_block("required_block", bt, config, "mongodbatlas")
    content = "\n".join(lines)
    assert "required_block {" in content
    assert "dynamic" not in content
    assert "var.required_block.name" in content


def test_render_required_list_block():
    bt = SchemaBlockType(
        nesting_mode=NestingMode.list,
        min_items=1,
        block=SchemaBlock(attributes={"value": SchemaAttribute(required=True)}),
    )
    config = GenerationTarget(resource_type="test")
    lines = render_block("items", bt, config, "mongodbatlas")
    content = "\n".join(lines)
    assert 'dynamic "items"' in content
    assert "for_each = var.items" in content
    assert "null" not in content


def test_generate_main_tf_with_meta_args():
    schema_raw = {"block": {"attributes": {"name": {"type": "string", "required": True}}}}
    schema = parse_resource_schema(schema_raw)
    config = GenerationTarget(
        resource_type="project",
        resource_tf=ResourceMetaArgs(
            count="var.create ? 1 : 0",
            depends_on=["module.vpc"],
            lifecycle="ignore_changes = [tags]",
        ),
    )
    output = generate_main_tf(schema, config, "mongodbatlas")
    assert 'resource "mongodbatlas_project" "this"' in output
    assert "count = var.create ? 1 : 0" in output
    assert "depends_on = [module.vpc]" in output
    assert "lifecycle {" in output
    assert "ignore_changes = [tags]" in output


def test_generate_main_tf_custom_label():
    schema_raw = {"block": {"attributes": {"id": {"type": "string", "computed": True}}}}
    schema = parse_resource_schema(schema_raw)
    config = GenerationTarget(resource_type="cluster", label="primary")
    output = generate_main_tf(schema, config, "mongodbatlas")
    assert '"primary"' in output


def test_generate_main_tf_excludes_computed_only(backup_schedule_schema: dict):
    schema = parse_resource_schema(backup_schedule_schema)
    config = GenerationTarget(resource_type="cloud_backup_schedule")
    output = generate_main_tf(schema, config, "mongodbatlas")
    assert "cluster_name" in output
    assert "cluster_id" not in output
    assert "next_snapshot" not in output


def test_generate_main_tf_single_variable_mode(project_schema: dict):
    schema = parse_resource_schema(project_schema)
    config = GenerationTarget(resource_type="project", use_single_variable=True)
    output = generate_main_tf(schema, config, "mongodbatlas")
    assert "var.mongodbatlas_project.name" in output
    assert "var.mongodbatlas_project.org_id" in output
