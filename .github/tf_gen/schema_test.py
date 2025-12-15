from __future__ import annotations

from tf_gen.schema.models import parse_resource_schema
from tf_gen.schema.types import AttrType, CollectionKind, NestingMode, TfTypeKind


def test_parse_primitive_types(backup_schedule_schema: dict):
    schema = parse_resource_schema(backup_schedule_schema)
    cluster_name = schema.block.attributes["cluster_name"]
    assert cluster_name.type
    assert cluster_name.type.kind == TfTypeKind.primitive
    assert cluster_name.type.primitive == AttrType.string
    assert cluster_name.required


def test_parse_collection_types(vpc_endpoint_schema: dict):
    schema = parse_resource_schema(vpc_endpoint_schema)
    cidr_blocks = schema.block.attributes["cidr_blocks"]
    assert cidr_blocks.type
    assert cidr_blocks.type.kind == TfTypeKind.collection
    assert cidr_blocks.type.collection_kind == CollectionKind.list
    assert cidr_blocks.type.element_type
    assert cidr_blocks.type.element_type.primitive == AttrType.string

    tags = schema.block.attributes["tags"]
    assert tags.type
    assert tags.type.collection_kind == CollectionKind.map


def test_parse_inline_object_type(vpc_endpoint_schema: dict):
    schema = parse_resource_schema(vpc_endpoint_schema)
    dns_entry = schema.block.attributes["dns_entry"]
    assert dns_entry.type
    assert dns_entry.type.kind == TfTypeKind.collection
    assert dns_entry.type.element_type
    assert dns_entry.type.element_type.kind == TfTypeKind.object
    assert dns_entry.type.element_type.object_attrs
    assert "dns_name" in dns_entry.type.element_type.object_attrs


def test_parse_nested_type(advanced_cluster_schema: dict):
    schema = parse_resource_schema(advanced_cluster_schema)
    adv_config = schema.block.attributes["advanced_configuration"]
    assert adv_config.nested_type
    assert adv_config.nested_type.nesting_mode == NestingMode.single
    assert "javascript_enabled" in adv_config.nested_type.attributes


def test_parse_block_types(backup_schedule_schema: dict):
    schema = parse_resource_schema(backup_schedule_schema)
    copy_settings = schema.block.block_types["copy_settings"]
    assert copy_settings.nesting_mode == NestingMode.list
    assert not copy_settings.is_required
    assert not copy_settings.is_single_object
    assert "cloud_provider" in copy_settings.block.attributes


def test_parse_block_type_max_items_1(backup_schedule_schema: dict):
    schema = parse_resource_schema(backup_schedule_schema)
    export = schema.block.block_types["export"]
    assert export.is_single_object
    assert export.max_items == 1


def test_parse_block_type_set_nesting(vpc_endpoint_schema: dict):
    schema = parse_resource_schema(vpc_endpoint_schema)
    subnet_config = schema.block.block_types["subnet_configuration"]
    assert subnet_config.nesting_mode == NestingMode.set


def test_parse_block_type_single_nesting(vpc_endpoint_schema: dict):
    schema = parse_resource_schema(vpc_endpoint_schema)
    timeouts = schema.block.block_types["timeouts"]
    assert timeouts.nesting_mode == NestingMode.single


def test_attribute_flags(backup_schedule_schema: dict):
    schema = parse_resource_schema(backup_schedule_schema)
    cluster_name = schema.block.attributes["cluster_name"]
    assert cluster_name.required

    cluster_id = schema.block.attributes["cluster_id"]
    assert cluster_id.computed
    assert not cluster_id.optional
    assert cluster_id.is_computed_only

    auto_export = schema.block.attributes["auto_export_enabled"]
    assert auto_export.computed
    assert auto_export.optional
    assert not auto_export.is_computed_only


def test_deprecated_attribute(backup_schedule_schema: dict):
    schema = parse_resource_schema(backup_schedule_schema)
    copy_settings = schema.block.block_types["copy_settings"]
    replication_spec_id = copy_settings.block.attributes["replication_spec_id"]
    assert replication_spec_id.deprecated
