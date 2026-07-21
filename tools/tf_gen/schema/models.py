from __future__ import annotations

from typing import Self

from pydantic import BaseModel, Field, model_validator

from tf_gen.schema.types import AttrType, CollectionKind, NestingMode, TfTypeKind


class TfType(BaseModel):
    kind: TfTypeKind
    primitive: AttrType | None = None
    collection_kind: CollectionKind | None = None
    element_type: TfType | None = None
    object_attrs: dict[str, TfType] | None = None

    @classmethod
    def from_primitive(cls, primitive: AttrType) -> Self:
        return cls(kind=TfTypeKind.primitive, primitive=primitive)

    @classmethod
    def from_collection(cls, collection_kind: CollectionKind, element_type: TfType) -> Self:
        return cls(
            kind=TfTypeKind.collection,
            collection_kind=collection_kind,
            element_type=element_type,
        )

    @classmethod
    def from_object(cls, attrs: dict[str, TfType]) -> Self:
        return cls(kind=TfTypeKind.object, object_attrs=attrs)


class SchemaBlock(BaseModel):
    attributes: dict[str, SchemaAttribute] = Field(default_factory=dict)
    block_types: dict[str, SchemaBlockType] = Field(default_factory=dict)
    nesting_mode: NestingMode | None = None
    description: str | None = None
    deprecated: bool = False


class SchemaAttribute(BaseModel):
    type: TfType | None = None
    nested_type: SchemaBlock | None = None
    optional: bool = False
    required: bool = False
    computed: bool = False
    deprecated: bool = False
    deprecated_message: str | None = None
    sensitive: bool = False
    description: str | None = None

    @property
    def is_computed_only(self) -> bool:
        return self.computed and not self.optional and not self.required

    @property
    def is_output_candidate(self) -> bool:
        return self.computed and not self.required


class SchemaBlockType(BaseModel):
    nesting_mode: NestingMode
    block: SchemaBlock
    min_items: int | None = None
    max_items: int | None = None
    required: bool | None = None
    description: str | None = None
    deprecated: bool = False

    @property
    def is_required(self) -> bool:
        return (self.min_items or 0) > 0 or bool(self.required)

    @property
    def is_single_object(self) -> bool:
        return self.max_items == 1


class ResourceSchema(BaseModel):
    block: SchemaBlock
    version: int = 0

    @model_validator(mode="before")
    @classmethod
    def parse_raw_schema(cls, data: dict) -> dict:
        if "block" in data and isinstance(data["block"], dict):
            data["block"] = parse_block(data["block"])
        return data


def _parse_inline_type(value: str | list | dict) -> TfType:
    if isinstance(value, str):
        return TfType.from_primitive(AttrType.from_schema(value))
    if isinstance(value, list) and len(value) >= 2:
        if value[0] in ("list", "set", "map"):
            collection_kind = CollectionKind(value[0])
            elem_type = _parse_inline_type(value[1])
            return TfType.from_collection(collection_kind, elem_type)
        if value[0] == "object" and isinstance(value[1], dict):
            obj_attrs = {k: _parse_inline_type(v) for k, v in value[1].items()}
            return TfType.from_object(obj_attrs)
    if isinstance(value, dict):
        obj_attrs = {k: _parse_inline_type(v) for k, v in value.items()}
        return TfType.from_object(obj_attrs)
    return TfType.from_primitive(AttrType.dynamic)


def parse_type_field(
    type_field: str | list | None, element_type_field: str | dict | None = None
) -> TfType | None:
    if type_field is None:
        return None
    if isinstance(type_field, str):
        return TfType.from_primitive(AttrType.from_schema(type_field))
    if isinstance(type_field, list) and len(type_field) >= 2:
        collection_kind = CollectionKind(type_field[0])
        elem = element_type_field if element_type_field is not None else type_field[1]
        elem_type = _parse_inline_type(elem)
        return TfType.from_collection(collection_kind, elem_type)
    return TfType.from_primitive(AttrType.dynamic)


def parse_attribute(raw: dict) -> SchemaAttribute:
    type_ = parse_type_field(raw.get("type"), raw.get("element_type"))
    nested_type = None
    if nested_raw := raw.get("nested_type"):
        nesting_mode = NestingMode(nested_raw.get("nesting_mode", "single"))
        nested_type = parse_block(nested_raw)
        nested_type.nesting_mode = nesting_mode
    return SchemaAttribute(
        type=type_,
        nested_type=nested_type,
        optional=raw.get("optional", False),
        required=raw.get("required", False),
        computed=raw.get("computed", False),
        deprecated=raw.get("deprecated", False),
        deprecated_message=raw.get("deprecated_message"),
        sensitive=raw.get("sensitive", False),
        description=raw.get("description"),
    )


def parse_block_type(raw: dict) -> SchemaBlockType:
    return SchemaBlockType(
        nesting_mode=NestingMode(raw.get("nesting_mode", "list")),
        block=parse_block(raw.get("block", {})),
        min_items=raw.get("min_items"),
        max_items=raw.get("max_items"),
        required=raw.get("required"),
        description=raw.get("description"),
        deprecated=raw.get("deprecated", False),
    )


def parse_block(raw: dict) -> SchemaBlock:
    attributes = {name: parse_attribute(attr) for name, attr in raw.get("attributes", {}).items()}
    block_types = {name: parse_block_type(bt) for name, bt in raw.get("block_types", {}).items()}
    return SchemaBlock(
        attributes=attributes,
        block_types=block_types,
        description=raw.get("description"),
        deprecated=raw.get("deprecated", False),
    )


def parse_resource_schema(raw: dict) -> ResourceSchema:
    return ResourceSchema(
        block=parse_block(raw.get("block", {})),
        version=raw.get("version", 0),
    )
