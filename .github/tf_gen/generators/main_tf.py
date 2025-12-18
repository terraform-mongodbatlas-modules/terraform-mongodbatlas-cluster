from __future__ import annotations

from tf_gen.config import GenerationTarget
from tf_gen.generators.hcl_write import format_terraform
from tf_gen.schema.models import (
    ResourceSchema,
    SchemaAttribute,
    SchemaBlock,
    SchemaBlockType,
)
from tf_gen.schema.types import NestingMode


def should_include_in_resource(
    name: str, attr: SchemaAttribute | None, config: GenerationTarget
) -> bool:
    if name in config.variables_excluded:
        return False
    if attr and attr.is_computed_only:
        return False
    if name == "id" and not config.include_id_field:
        return False
    return True


def build_var_ref(name: str, config: GenerationTarget, provider_name: str) -> str:
    if override := config.resource_tf_var_overrides.get(name):
        return override
    var_name = f"{config.variables_prefix}{name}" if config.variables_prefix else name
    if config.use_single_variable:
        return f"var.{provider_name}_{config.resource_type}.{var_name}"
    return f"var.{var_name}"


def _render_direct_assignments(
    block: SchemaBlock, var_ref: str, indent: str = "    "
) -> list[str]:
    lines: list[str] = []
    for attr_name, attr in sorted(block.attributes.items()):
        if attr.is_computed_only:
            continue
        lines.append(f"{indent}{attr_name} = {var_ref}.{attr_name}")
    return lines


def _render_content_assignments(
    block: SchemaBlock, iterator: str, indent: str = "      "
) -> list[str]:
    lines: list[str] = []
    for attr_name, attr in sorted(block.attributes.items()):
        if attr.is_computed_only:
            continue
        lines.append(f"{indent}{attr_name} = {iterator}.value.{attr_name}")

    for bt_name, nested_bt in sorted(block.block_types.items()):
        nested_ref = f"{iterator}.value.{bt_name}"
        lines.extend(_render_nested_block(bt_name, nested_bt, nested_ref, indent))
    return lines


def _render_nested_block(
    name: str, bt: SchemaBlockType, parent_ref: str, indent: str = "      "
) -> list[str]:
    is_single = bt.is_single_object or bt.nesting_mode == NestingMode.single
    if is_single:
        for_each = f"{parent_ref} == null ? [] : [{parent_ref}]"
    else:
        for_each = f"{parent_ref} == null ? [] : {parent_ref}"

    nested_indent = indent + "  "
    content_indent = nested_indent + "  "

    lines = [
        f'{indent}dynamic "{name}" {{',
        f"{nested_indent}for_each = {for_each}",
        f"{nested_indent}content {{",
    ]
    lines.extend(_render_content_assignments(bt.block, name, content_indent))
    lines.append(f"{nested_indent}}}")
    lines.append(f"{indent}}}")
    return lines


def _render_required_block(
    name: str, bt: SchemaBlockType, var_ref: str, indent: str = "  "
) -> list[str]:
    is_single = bt.is_single_object or bt.nesting_mode == NestingMode.single
    if is_single:
        lines = [f"{indent}{name} {{"]
        lines.extend(_render_direct_assignments(bt.block, var_ref, indent + "  "))
        lines.append(f"{indent}}}")
        return lines
    return _render_dynamic_block(name, bt, var_ref, indent, is_required=True)


def _render_dynamic_block(
    name: str,
    bt: SchemaBlockType,
    var_ref: str,
    indent: str = "  ",
    is_required: bool = False,
) -> list[str]:
    is_single = bt.is_single_object or bt.nesting_mode == NestingMode.single
    if is_required:
        for_each = var_ref
    elif is_single:
        for_each = f"{var_ref} == null ? [] : [{var_ref}]"
    else:
        for_each = f"{var_ref} == null ? [] : {var_ref}"

    nested_indent = indent + "  "
    content_indent = nested_indent + "  "

    lines = [
        f'{indent}dynamic "{name}" {{',
        f"{nested_indent}for_each = {for_each}",
        f"{nested_indent}content {{",
    ]
    lines.extend(_render_content_assignments(bt.block, name, content_indent))
    lines.append(f"{nested_indent}}}")
    lines.append(f"{indent}}}")
    return lines


def render_block(
    name: str, bt: SchemaBlockType, config: GenerationTarget, provider_name: str
) -> list[str]:
    var_ref = build_var_ref(name, config, provider_name)

    if bt.is_required:
        return _render_required_block(name, bt, var_ref)
    return _render_dynamic_block(name, bt, var_ref)


def generate_main_tf(
    schema: ResourceSchema, config: GenerationTarget, provider_name: str
) -> str:
    full_type = f"{provider_name}_{config.resource_type}"
    lines = [f'resource "{full_type}" "{config.label}" {{']

    meta = config.resource_tf
    if meta.count:
        lines.append(f"  count = {meta.count}")
    if meta.provider:
        lines.append(f"  provider = {meta.provider}")

    # Collect and sort attributes
    attr_lines: list[str] = []
    for name, attr in sorted(schema.block.attributes.items()):
        if not should_include_in_resource(name, attr, config):
            continue
        var_ref = build_var_ref(name, config, provider_name)
        attr_lines.append(f"  {name} = {var_ref}")

    lines.extend(attr_lines)

    # Block types
    for name, bt in sorted(schema.block.block_types.items()):
        if name in config.variables_excluded:
            continue
        lines.append("")
        lines.extend(render_block(name, bt, config, provider_name))

    # Lifecycle and depends_on at end
    if meta.depends_on:
        deps = ", ".join(meta.depends_on)
        lines.append("")
        lines.append(f"  depends_on = [{deps}]")
    if meta.lifecycle:
        lines.append("")
        lines.append("  lifecycle {")
        for lc_line in meta.lifecycle.strip().split("\n"):
            lines.append(f"    {lc_line.strip()}")
        lines.append("  }")

    lines.append("}")
    return format_terraform("\n".join(lines))
