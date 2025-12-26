from __future__ import annotations

import logging

from tf_gen.config import GenerationTarget, OutputAttributeOverride
from tf_gen.generators.outputs_tf import (
    build_resource_refs,
    generate_outputs_tf,
    should_generate_output,
)
from tf_gen.schema.models import (
    ResourceSchema,
    SchemaAttribute,
    SchemaBlock,
    TfType,
    parse_resource_schema,
)
from tf_gen.schema.types import AttrType


def test_should_generate_output_computed_only():
    attr = SchemaAttribute(type=TfType.from_primitive(AttrType.string), computed=True)
    assert should_generate_output("id", attr, GenerationTarget())


def test_should_generate_output_computed_optional():
    attr = SchemaAttribute(
        type=TfType.from_primitive(AttrType.bool), computed=True, optional=True
    )
    assert should_generate_output("enabled", attr, GenerationTarget())


def test_should_generate_output_excludes_required():
    attr = SchemaAttribute(
        type=TfType.from_primitive(AttrType.string), computed=True, required=True
    )
    assert not should_generate_output("name", attr, GenerationTarget())


def test_should_generate_output_excluded_list():
    attr = SchemaAttribute(type=TfType.from_primitive(AttrType.string), computed=True)
    config = GenerationTarget(outputs_excluded=["id"])
    assert not should_generate_output("id", attr, config)


def test_build_resource_refs():
    config = GenerationTarget(label="this")
    base, indexed = build_resource_refs("mongodbatlas", "project", config)
    assert base == "mongodbatlas_project.this"
    assert indexed == "mongodbatlas_project.this"


def test_build_resource_refs_with_count():
    config = GenerationTarget(label="main", use_resource_count=True)
    base, indexed = build_resource_refs("mongodbatlas", "project", config)
    assert base == "mongodbatlas_project.main"
    assert indexed == "mongodbatlas_project.main[0]"


def test_computed_only_output(project_schema: dict):
    schema = parse_resource_schema(project_schema)
    config = GenerationTarget(resource_type="project")
    output = generate_outputs_tf(schema, config, "mongodbatlas")
    assert 'output "id"' in output
    assert 'output "created"' in output
    assert "mongodbatlas_project.this.id" in output


def test_computed_optional_output(project_schema: dict):
    schema = parse_resource_schema(project_schema)
    config = GenerationTarget(resource_type="project")
    output = generate_outputs_tf(schema, config, "mongodbatlas")
    assert 'output "is_data_explorer_enabled"' in output


def test_skip_required_attributes(project_schema: dict):
    schema = parse_resource_schema(project_schema)
    config = GenerationTarget(resource_type="project")
    output = generate_outputs_tf(schema, config, "mongodbatlas")
    assert 'output "name"' not in output
    assert 'output "org_id"' not in output


def test_block_type_computed_children(project_schema: dict):
    schema = parse_resource_schema(project_schema)
    config = GenerationTarget(resource_type="project")
    output = generate_outputs_tf(schema, config, "mongodbatlas")
    assert 'output "limits_current_usage"' in output
    assert "limits[*].current_usage" in output


def test_single_nested_children(advanced_cluster_schema: dict):
    schema = parse_resource_schema(advanced_cluster_schema)
    config = GenerationTarget(resource_type="advanced_cluster")
    output = generate_outputs_tf(schema, config, "mongodbatlas")
    assert 'output "bi_connector_config"' in output
    assert 'output "bi_connector_config_enabled"' in output
    assert "bi_connector_config == null ? null : " in output


def test_skip_children_over_threshold(advanced_cluster_schema: dict):
    schema = parse_resource_schema(advanced_cluster_schema)
    config = GenerationTarget(
        resource_type="advanced_cluster", output_attribute_max_children=2
    )
    output = generate_outputs_tf(schema, config, "mongodbatlas")
    assert 'output "bi_connector_config_enabled"' in output  # 2 children <= 2
    assert (
        'output "advanced_configuration_javascript_enabled"' not in output
    )  # 13 children > 2


def test_include_children_override_true(advanced_cluster_schema: dict):
    schema = parse_resource_schema(advanced_cluster_schema)
    config = GenerationTarget(
        resource_type="advanced_cluster",
        output_attribute_max_children=1,
        output_tf_overrides={
            "bi_connector_config": OutputAttributeOverride(include_children=True)
        },
    )
    output = generate_outputs_tf(schema, config, "mongodbatlas")
    assert 'output "bi_connector_config_enabled"' in output


def test_include_children_override_false(advanced_cluster_schema: dict):
    schema = parse_resource_schema(advanced_cluster_schema)
    config = GenerationTarget(
        resource_type="advanced_cluster",
        output_tf_overrides={
            "bi_connector_config": OutputAttributeOverride(include_children=False)
        },
    )
    output = generate_outputs_tf(schema, config, "mongodbatlas")
    assert 'output "bi_connector_config"' in output
    assert 'output "bi_connector_config_enabled"' not in output


def test_output_name_override(project_schema: dict):
    schema = parse_resource_schema(project_schema)
    config = GenerationTarget(
        resource_type="project",
        output_tf_overrides={"id": OutputAttributeOverride(name="project_id")},
    )
    output = generate_outputs_tf(schema, config, "mongodbatlas")
    assert 'output "project_id"' in output


def test_output_value_override(project_schema: dict):
    schema = parse_resource_schema(project_schema)
    config = GenerationTarget(
        resource_type="project",
        output_tf_overrides={
            "id": OutputAttributeOverride(value="upper(mongodbatlas_project.this.id)")
        },
    )
    output = generate_outputs_tf(schema, config, "mongodbatlas")
    assert "upper(mongodbatlas_project.this.id)" in output


def test_deprecated_output(project_schema: dict):
    schema = parse_resource_schema(project_schema)
    config = GenerationTarget(resource_type="project")
    output = generate_outputs_tf(schema, config, "mongodbatlas")
    assert 'output "ip_addresses"' in output
    assert "DEPRECATED" in output


def test_set_warning_logged(project_schema: dict, caplog):
    schema = parse_resource_schema(project_schema)
    config = GenerationTarget(resource_type="project")
    with caplog.at_level(logging.WARNING):
        generate_outputs_tf(schema, config, "mongodbatlas", log=logging.getLogger())
    assert any(
        "limits_current_usage" in r.message and "set splat" in r.message
        for r in caplog.records
    )


def test_outputs_excluded_parent_keeps_children(advanced_cluster_schema: dict):
    schema = parse_resource_schema(advanced_cluster_schema)
    config = GenerationTarget(
        resource_type="advanced_cluster", outputs_excluded=["bi_connector_config"]
    )
    output = generate_outputs_tf(schema, config, "mongodbatlas")
    assert 'output "bi_connector_config"' not in output
    assert 'output "bi_connector_config_enabled"' in output


def _schema_with_sensitive_attr() -> ResourceSchema:
    return ResourceSchema(
        block=SchemaBlock(
            attributes={
                "secret_key": SchemaAttribute(
                    type=TfType.from_primitive(AttrType.string),
                    computed=True,
                    sensitive=True,
                )
            }
        )
    )


def test_sensitive_output_from_schema():
    schema = _schema_with_sensitive_attr()
    config = GenerationTarget(resource_type="test")
    output = generate_outputs_tf(schema, config, "test")
    assert 'output "secret_key"' in output
    assert "sensitive = true" in output


def test_sensitive_override_true(project_schema: dict):
    schema = parse_resource_schema(project_schema)
    config = GenerationTarget(
        resource_type="project",
        output_tf_overrides={"id": OutputAttributeOverride(sensitive=True)},
    )
    output = generate_outputs_tf(schema, config, "mongodbatlas")
    assert 'output "id"' in output
    assert "sensitive = true" in output


def test_sensitive_override_false():
    schema = _schema_with_sensitive_attr()
    config = GenerationTarget(
        resource_type="test",
        output_tf_overrides={"secret_key": OutputAttributeOverride(sensitive=False)},
    )
    output = generate_outputs_tf(schema, config, "test")
    assert 'output "secret_key"' in output
    assert "sensitive = true" not in output


def test_count_safe_wrapping(project_schema: dict):
    schema = parse_resource_schema(project_schema)
    config = GenerationTarget(resource_type="project", use_resource_count=True)
    output = generate_outputs_tf(schema, config, "mongodbatlas")
    assert "length(mongodbatlas_project.this) > 0 ?" in output
    assert ": null" in output


def test_outputs_prefix(project_schema: dict):
    schema = parse_resource_schema(project_schema)
    config = GenerationTarget(resource_type="project", outputs_prefix="main_")
    output = generate_outputs_tf(schema, config, "mongodbatlas")
    assert 'output "main_id"' in output
    assert 'output "main_created"' in output


def test_single_output_mode(project_schema: dict):
    schema = parse_resource_schema(project_schema)
    config = GenerationTarget(resource_type="project", use_single_output=True)
    output = generate_outputs_tf(schema, config, "mongodbatlas")
    assert 'output "project"' in output
    assert "value = {" in output
    assert "id = mongodbatlas_project.this.id" in output


def test_single_output_with_count(project_schema: dict):
    schema = parse_resource_schema(project_schema)
    config = GenerationTarget(
        resource_type="project", use_single_output=True, use_resource_count=True
    )
    output = generate_outputs_tf(schema, config, "mongodbatlas")
    assert "length(mongodbatlas_project.this) > 0 ? {" in output
    assert "} : null" in output


def test_single_output_with_prefix(project_schema: dict):
    schema = parse_resource_schema(project_schema)
    config = GenerationTarget(
        resource_type="project", use_single_output=True, outputs_prefix="primary_"
    )
    output = generate_outputs_tf(schema, config, "mongodbatlas")
    assert 'output "primary_project"' in output
