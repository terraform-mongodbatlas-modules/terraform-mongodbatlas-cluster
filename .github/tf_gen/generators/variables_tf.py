from __future__ import annotations

from pydantic import BaseModel
from tf_gen.config import GenerationTarget
from tf_gen.generators.hcl_write import (
    make_description,
    render_blocks,
    render_description,
)
from tf_gen.schema.models import (
    ResourceSchema,
    SchemaAttribute,
    SchemaBlock,
    SchemaBlockType,
    TfType,
)
from tf_gen.schema.types import AttrType, NestingMode, TfTypeKind


class VariableSpec(BaseModel):
    name: str
    type_str: str
    description: str | None = None
    default: str | None = None
    nullable: bool = False
    sensitive: bool = False


def _render_object_fields(fields: list[str], indent: int = 0) -> str:
    if not fields:
        return "object({})"
    prefix = "  " * indent
    inner_prefix = "  " * (indent + 1)
    lines = [f"{inner_prefix}{f}" for f in fields]
    return f"object({{\n{',\n'.join(lines)}\n{prefix}}})"


def render_tf_type(tf_type: TfType, indent: int = 0) -> str:
    match tf_type.kind:
        case TfTypeKind.primitive:
            return "any" if tf_type.primitive == AttrType.dynamic else tf_type.primitive  # pyright: ignore[reportReturnType]
        case TfTypeKind.collection:
            elem = (
                render_tf_type(tf_type.element_type, indent)
                if tf_type.element_type
                else "any"
            )
            return f"{tf_type.collection_kind}({elem})"
        case TfTypeKind.object:
            if not tf_type.object_attrs:
                return "object({})"
            fields = [
                f"{k} = {render_tf_type(v, indent + 1)}"
                for k, v in sorted(tf_type.object_attrs.items())
            ]
            return _render_object_fields(fields, indent)
    raise ValueError(f"Unknown TF type kind: {tf_type.kind}")


def _render_object_type_with_optionality(
    attrs: dict[str, SchemaAttribute],
    block_types: dict[str, SchemaBlockType] | None = None,
    indent: int = 0,
) -> str:
    """Render object type with optional() for optional fields."""
    fields = []
    for name, attr in sorted(attrs.items()):
        if attr.is_computed_only:
            continue
        field_type = _get_attr_type_str(attr, indent + 1)
        if attr.required:
            fields.append(f"{name} = {field_type}")
        else:
            fields.append(f"{name} = optional({field_type})")

    if block_types:
        for name, bt in sorted(block_types.items()):
            bt_type = _get_block_type_str(bt, indent + 1)
            if bt.is_required:
                fields.append(f"{name} = {bt_type}")
            else:
                fields.append(f"{name} = optional({bt_type})")

    return _render_object_fields(fields, indent)


def _get_attr_type_str(attr: SchemaAttribute, indent: int = 0) -> str:
    if attr.nested_type:
        return _render_nested_type(attr.nested_type, indent)
    if attr.type:
        return render_tf_type(attr.type, indent)
    return "any"


def _render_nested_type(nested: SchemaBlock, indent: int = 0) -> str:
    obj_type = _render_object_type_with_optionality(
        nested.attributes, nested.block_types, indent
    )
    match nested.nesting_mode:
        case NestingMode.single | None:
            return obj_type
        case NestingMode.list:
            return f"list({obj_type})"
        case NestingMode.set:
            return f"set({obj_type})"
    return obj_type


def _get_block_type_str(bt: SchemaBlockType, indent: int = 0) -> str:
    obj_type = _render_object_type_with_optionality(
        bt.block.attributes, bt.block.block_types, indent
    )
    if bt.is_single_object:
        return obj_type
    match bt.nesting_mode:
        case NestingMode.list:
            return f"list({obj_type})"
        case NestingMode.set:
            return f"set({obj_type})"
        case NestingMode.single:
            return obj_type
    return obj_type


def should_generate_variable(
    name: str, attr: SchemaAttribute, config: GenerationTarget
) -> bool:
    if attr.is_computed_only:
        return False
    if name == "id" and not config.include_id_field:
        return False
    if name in config.variables_excluded:
        return False
    return True


def _apply_overrides(
    spec: VariableSpec, name: str, config: GenerationTarget
) -> VariableSpec:
    overrides = config.variable_tf.get(name, {})
    if override_name := overrides.get("name"):
        spec.name = override_name
    if override_desc := overrides.get("description"):
        spec.description = override_desc
    if override_type := overrides.get("type"):
        spec.type_str = override_type
    if "default" in overrides:
        spec.default = overrides["default"]
        spec.nullable = spec.default == "null"
    if "sensitive" in overrides:
        spec.sensitive = overrides["sensitive"]
    return spec


def _determine_required(
    name: str, is_schema_required: bool, config: GenerationTarget
) -> bool:
    if name in config.variables_required:
        return True
    if config.all_variables_optional:
        return False
    return is_schema_required


def attr_to_variable_spec(
    name: str, attr: SchemaAttribute, config: GenerationTarget
) -> VariableSpec:
    var_name = f"{config.variables_prefix}{name}" if config.variables_prefix else name
    type_str = _get_attr_type_str(attr)
    description = make_description(
        attr.description, attr.deprecated, attr.deprecated_message
    )
    is_required = _determine_required(name, attr.required, config)
    spec = VariableSpec(
        name=var_name,
        type_str=type_str,
        description=description,
        default=None if is_required else "null",
        nullable=not is_required,
        sensitive=attr.sensitive,
    )
    return _apply_overrides(spec, name, config)


def block_type_to_variable_spec(
    name: str, bt: SchemaBlockType, config: GenerationTarget
) -> VariableSpec:
    var_name = f"{config.variables_prefix}{name}" if config.variables_prefix else name
    type_str = _get_block_type_str(bt)
    description = make_description(bt.description, bt.deprecated)
    is_required = _determine_required(name, bt.is_required, config)
    spec = VariableSpec(
        name=var_name,
        type_str=type_str,
        description=description,
        default=None if is_required else "null",
        nullable=not is_required,
    )
    return _apply_overrides(spec, name, config)


def render_variable_block(spec: VariableSpec) -> str:
    lines = [f'variable "{spec.name}" {{', f"  type = {spec.type_str}"]
    if spec.description:
        lines.append(f"  description = {render_description(spec.description)}")
    if spec.nullable:
        lines.append("  nullable = true")
    if spec.default is not None:
        lines.append(f"  default = {spec.default}")
    if spec.sensitive:
        lines.append("  sensitive = true")
    lines.append("}")
    return "\n".join(lines)


def _build_single_variable_spec(
    specs: list[VariableSpec], provider_name: str, resource_type: str
) -> VariableSpec:
    var_name = f"{provider_name}_{resource_type}"
    fields = []
    for s in specs:
        field_type = s.type_str
        if s.nullable:
            fields.append(f"{s.name} = optional({field_type})")
        else:
            fields.append(f"{s.name} = {field_type}")
    type_str = _render_object_fields(fields, indent=0)
    return VariableSpec(name=var_name, type_str=type_str, default=None, nullable=False)


def generate_variables_tf(
    schema: ResourceSchema, config: GenerationTarget, provider_name: str
) -> str:
    specs: list[VariableSpec] = []

    for name, attr in schema.block.attributes.items():
        if should_generate_variable(name, attr, config):
            specs.append(attr_to_variable_spec(name, attr, config))

    for name, bt in schema.block.block_types.items():
        if name not in config.variables_excluded:
            specs.append(block_type_to_variable_spec(name, bt, config))

    specs.sort(key=lambda s: (s.nullable, s.name))

    if config.use_single_variable:
        single_spec = _build_single_variable_spec(
            specs, provider_name, config.resource_type
        )
        return render_blocks([single_spec], render_variable_block)

    return render_blocks(specs, render_variable_block)
