from __future__ import annotations

from tf_gen.config import GenerationTarget
from tf_gen.generators.variables_tf import (
    DEPRECATED_PREFIX,
    attr_to_variable_spec,
    block_type_to_variable_spec,
    generate_variables_tf,
    render_tf_type,
    render_variable_block,
    should_generate_variable,
)
from tf_gen.schema.models import (
    SchemaAttribute,
    TfType,
    parse_resource_schema,
)
from tf_gen.schema.types import AttrType, CollectionKind


def test_render_primitive_types():
    assert render_tf_type(TfType.from_primitive(AttrType.string)) == "string"
    assert render_tf_type(TfType.from_primitive(AttrType.bool)) == "bool"
    assert render_tf_type(TfType.from_primitive(AttrType.number)) == "number"
    assert render_tf_type(TfType.from_primitive(AttrType.dynamic)) == "any"


def test_render_collection_types():
    elem = TfType.from_primitive(AttrType.string)
    assert (
        render_tf_type(TfType.from_collection(CollectionKind.list, elem))
        == "list(string)"
    )
    assert (
        render_tf_type(TfType.from_collection(CollectionKind.set, elem))
        == "set(string)"
    )
    assert (
        render_tf_type(TfType.from_collection(CollectionKind.map, elem))
        == "map(string)"
    )


def test_render_object_type():
    obj = TfType.from_object(
        {
            "name": TfType.from_primitive(AttrType.string),
            "count": TfType.from_primitive(AttrType.number),
        }
    )
    assert render_tf_type(obj) == "object({count = number, name = string})"


def test_should_generate_variable_computed_only(backup_schedule_schema: dict):
    schema = parse_resource_schema(backup_schedule_schema)
    config = GenerationTarget()
    cluster_id = schema.block.attributes["cluster_id"]
    assert not should_generate_variable("cluster_id", cluster_id, config)


def test_should_generate_variable_excludes_id_by_default(backup_schedule_schema: dict):
    schema = parse_resource_schema(backup_schedule_schema)
    config = GenerationTarget()
    id_attr = schema.block.attributes["id"]
    assert not should_generate_variable("id", id_attr, config)
    config_with_id = GenerationTarget(include_id_field=True)
    assert should_generate_variable("id", id_attr, config_with_id)


def test_should_generate_variable_excluded(backup_schedule_schema: dict):
    schema = parse_resource_schema(backup_schedule_schema)
    config = GenerationTarget(variables_excluded=["cluster_name"])
    cluster_name = schema.block.attributes["cluster_name"]
    assert not should_generate_variable("cluster_name", cluster_name, config)


def test_attr_to_variable_required(backup_schedule_schema: dict):
    schema = parse_resource_schema(backup_schedule_schema)
    config = GenerationTarget()
    spec = attr_to_variable_spec(
        "cluster_name", schema.block.attributes["cluster_name"], config
    )
    assert spec.name == "cluster_name"
    assert spec.type_str == "string"
    assert not spec.nullable
    assert spec.default is None


def test_attr_to_variable_optional(backup_schedule_schema: dict):
    schema = parse_resource_schema(backup_schedule_schema)
    config = GenerationTarget()
    spec = attr_to_variable_spec(
        "auto_export_enabled", schema.block.attributes["auto_export_enabled"], config
    )
    assert spec.nullable
    assert spec.default == "null"


def test_attr_to_variable_with_prefix():
    attr = SchemaAttribute(type=TfType.from_primitive(AttrType.string), required=True)
    config = GenerationTarget(variables_prefix="atlas_")
    spec = attr_to_variable_spec("name", attr, config)
    assert spec.name == "atlas_name"


def test_attr_to_variable_deprecated(backup_schedule_schema: dict):
    schema = parse_resource_schema(backup_schedule_schema)
    copy_settings = schema.block.block_types["copy_settings"]
    repl_spec_id = copy_settings.block.attributes["replication_spec_id"]
    config = GenerationTarget()
    spec = attr_to_variable_spec("replication_spec_id", repl_spec_id, config)
    assert spec.description is not None
    assert spec.description.startswith(DEPRECATED_PREFIX)


def test_attr_to_variable_sensitive(database_user_schema: dict):
    schema = parse_resource_schema(database_user_schema)
    config = GenerationTarget()
    spec = attr_to_variable_spec(
        "password", schema.block.attributes["password"], config
    )
    assert spec.sensitive


def test_block_type_list_variable(backup_schedule_schema: dict):
    schema = parse_resource_schema(backup_schedule_schema)
    config = GenerationTarget()
    spec = block_type_to_variable_spec(
        "copy_settings", schema.block.block_types["copy_settings"], config
    )
    assert spec.type_str.startswith("list(object(")
    assert spec.nullable


def test_block_type_single_object(backup_schedule_schema: dict):
    schema = parse_resource_schema(backup_schedule_schema)
    config = GenerationTarget()
    spec = block_type_to_variable_spec(
        "export", schema.block.block_types["export"], config
    )
    assert spec.type_str.startswith("object(")
    assert not spec.type_str.startswith("list(")


def test_block_type_set_nesting(project_schema: dict):
    schema = parse_resource_schema(project_schema)
    config = GenerationTarget()
    spec = block_type_to_variable_spec(
        "limits", schema.block.block_types["limits"], config
    )
    assert spec.type_str.startswith("set(object(")


def test_nested_type_single(advanced_cluster_schema: dict):
    schema = parse_resource_schema(advanced_cluster_schema)
    config = GenerationTarget()
    spec = attr_to_variable_spec(
        "advanced_configuration",
        schema.block.attributes["advanced_configuration"],
        config,
    )
    assert spec.type_str.startswith("object(")
    assert "javascript_enabled" in spec.type_str


def test_variable_tf_overrides():
    attr = SchemaAttribute(type=TfType.from_primitive(AttrType.string), optional=True)
    config = GenerationTarget(
        variable_tf={
            "name": {
                "description": "Custom description",
                "sensitive": True,
            }
        }
    )
    spec = attr_to_variable_spec("name", attr, config)
    assert spec.description == "Custom description"
    assert spec.sensitive


def test_variables_required_override():
    attr = SchemaAttribute(type=TfType.from_primitive(AttrType.string), optional=True)
    config = GenerationTarget(variables_required=["name"])
    spec = attr_to_variable_spec("name", attr, config)
    assert not spec.nullable
    assert spec.default is None


def test_use_schema_computability_false():
    attr = SchemaAttribute(type=TfType.from_primitive(AttrType.string), required=True)
    config = GenerationTarget(use_schema_computability=False)
    spec = attr_to_variable_spec("name", attr, config)
    assert spec.nullable
    assert spec.default == "null"


def test_render_variable_block_required():
    spec = attr_to_variable_spec(
        "name",
        SchemaAttribute(
            type=TfType.from_primitive(AttrType.string),
            required=True,
            description="Project name",
        ),
        GenerationTarget(),
    )
    output = render_variable_block(spec)
    assert 'variable "name"' in output
    assert "type = string" in output
    assert "Project name" in output
    assert "nullable" not in output
    assert "default" not in output


def test_render_variable_block_optional():
    spec = attr_to_variable_spec(
        "enabled",
        SchemaAttribute(type=TfType.from_primitive(AttrType.bool), optional=True),
        GenerationTarget(),
    )
    output = render_variable_block(spec)
    assert "nullable = true" in output
    assert "default = null" in output


def test_generate_variables_tf_ordering(backup_schedule_schema: dict):
    schema = parse_resource_schema(backup_schedule_schema)
    config = GenerationTarget(resource_type="cloud_backup_schedule")
    output = generate_variables_tf(schema, config, "mongodbatlas")
    cluster_name_pos = output.find("cluster_name")
    auto_export_pos = output.find("auto_export_enabled")
    assert cluster_name_pos < auto_export_pos  # required before optional


def test_generate_variables_tf_single_variable(backup_schedule_schema: dict):
    schema = parse_resource_schema(backup_schedule_schema)
    config = GenerationTarget(
        resource_type="cloud_backup_schedule", use_single_variable=True
    )
    output = generate_variables_tf(schema, config, "mongodbatlas")
    assert 'variable "mongodbatlas_cloud_backup_schedule"' in output
    assert output.count('variable "') == 1


def test_generate_variables_tf_excludes_computed_only(backup_schedule_schema: dict):
    schema = parse_resource_schema(backup_schedule_schema)
    config = GenerationTarget(resource_type="cloud_backup_schedule")
    output = generate_variables_tf(schema, config, "mongodbatlas")
    assert "cluster_id" not in output
    assert "next_snapshot" not in output
    assert "id_policy" not in output
