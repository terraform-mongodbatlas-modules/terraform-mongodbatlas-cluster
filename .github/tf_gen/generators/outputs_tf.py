from __future__ import annotations

import logging
from dataclasses import dataclass, field

from pydantic import BaseModel
from tf_gen.config import GenerationTarget, OutputAttributeOverride
from tf_gen.generators.hcl_write import (
    make_description,
    render_blocks,
    render_description,
)
from tf_gen.schema.models import ResourceSchema, SchemaAttribute, SchemaBlockType
from tf_gen.schema.types import NestingMode

logger = logging.getLogger(__name__)


class OutputSpec(BaseModel):
    name: str
    value: str
    description: str | None = None
    sensitive: bool = False

    def apply_override(self, override: OutputAttributeOverride) -> OutputSpec:
        return OutputSpec(
            name=override.name if override.name else self.name,
            value=override.value if override.value else self.value,
            description=self.description,
            sensitive=override.sensitive
            if override.sensitive is not None
            else self.sensitive,
        )


@dataclass
class OutputCollector:
    base_ref: str
    indexed_ref: str
    config: GenerationTarget
    outputs: list[OutputSpec] = field(default_factory=list)
    set_outputs: set[str] = field(default_factory=set)

    def add(self, spec: OutputSpec, is_set: bool = False) -> None:
        self.outputs.append(spec)
        if is_set:
            self.set_outputs.add(spec.name)


def should_generate_output(
    name: str, attr: SchemaAttribute, config: GenerationTarget
) -> bool:
    if name in config.outputs_excluded:
        return False
    return attr.is_output_candidate


def build_resource_refs(
    provider_name: str, resource_type: str, config: GenerationTarget
) -> tuple[str, str]:
    """Returns (base_ref, indexed_ref). When not using count, both are the same."""
    base = f"{provider_name}_{resource_type}.{config.label}"
    if config.use_resource_count:
        return base, f"{base}[0]"
    return base, base


def _wrap_count_safe(base_ref: str, value_expr: str) -> str:
    """Wrap value expression with length check for count=0 safety."""
    length_check = f"length({base_ref}) > 0"
    # If value already has null check, convert to && short-circuit
    if " == null ? null : " in value_expr:
        parts = value_expr.split(" == null ? null : ", 1)
        return f"{length_check} && {parts[0]} != null ? {parts[1]} : null"
    return f"{length_check} ? {value_expr} : null"


def _build_value_expr(
    indexed_ref: str,
    parent_path: str | None,
    leaf: str,
    nesting: NestingMode | None,
    parent_optional: bool,
) -> str:
    if parent_path is None:
        return f"{indexed_ref}.{leaf}"

    full_ref = f"{indexed_ref}.{parent_path}"
    match nesting:
        case NestingMode.list | NestingMode.set:
            leaf_expr = f"{full_ref}[*].{leaf}"
            if parent_optional:
                return f"{full_ref} == null ? null : {leaf_expr}"
            return leaf_expr
        case NestingMode.single | None:
            leaf_expr = f"{full_ref}.{leaf}"
            if parent_optional:
                return f"{full_ref} == null ? null : {leaf_expr}"
            return leaf_expr


def _should_expand_children(
    name: str, attr: SchemaAttribute, config: GenerationTarget
) -> bool:
    if name in config.output_tf_overrides:
        override = config.output_tf_overrides[name]
        if override.include_children is not None:
            return override.include_children
    if attr.nested_type is None:
        return False
    child_count = len(attr.nested_type.attributes)
    return child_count <= config.output_attribute_max_children


def _collect_from_nested_attr(
    collector: OutputCollector,
    parent_name: str,
    attr: SchemaAttribute,
) -> None:
    if attr.nested_type is None:
        return
    parent_optional = not attr.required
    nesting = attr.nested_type.nesting_mode
    is_set = nesting == NestingMode.set

    for child_name, child_attr in attr.nested_type.attributes.items():
        output_name = f"{parent_name}_{child_name}"
        if output_name in collector.config.outputs_excluded:
            continue
        value = _build_value_expr(
            collector.indexed_ref, parent_name, child_name, nesting, parent_optional
        )
        spec = OutputSpec(
            name=output_name,
            value=value,
            description=child_attr.description,
            sensitive=child_attr.sensitive,
        )
        collector.add(spec, is_set=is_set)


def collect_from_attributes(
    attrs: dict[str, SchemaAttribute],
    collector: OutputCollector,
) -> None:
    for name, attr in attrs.items():
        if not attr.is_output_candidate:
            continue
        # Add parent output unless excluded
        if name not in collector.config.outputs_excluded:
            value = f"{collector.indexed_ref}.{name}"
            desc = make_description(
                attr.description, attr.deprecated, attr.deprecated_message
            )
            is_set = (
                attr.nested_type and attr.nested_type.nesting_mode == NestingMode.set
            )
            collector.add(
                OutputSpec(
                    name=name, value=value, description=desc, sensitive=attr.sensitive
                ),
                is_set=bool(is_set),
            )
        # Expand children regardless of parent exclusion
        if _should_expand_children(name, attr, collector.config):
            _collect_from_nested_attr(collector, name, attr)


def collect_from_block_types(
    block_types: dict[str, SchemaBlockType],
    collector: OutputCollector,
) -> None:
    for bt_name, bt in block_types.items():
        if bt_name in collector.config.outputs_excluded:
            continue
        nesting = bt.nesting_mode
        parent_optional = not bt.is_required
        is_set = nesting == NestingMode.set

        computed_children = [
            (name, attr)
            for name, attr in bt.block.attributes.items()
            if attr.is_output_candidate
        ]
        if len(computed_children) > collector.config.output_attribute_max_children:
            computed_children = sorted(computed_children, key=lambda x: x[0])[
                : collector.config.output_attribute_max_children
            ]

        for child_name, child_attr in computed_children:
            output_name = f"{bt_name}_{child_name}"
            if output_name in collector.config.outputs_excluded:
                continue
            value = _build_value_expr(
                collector.indexed_ref, bt_name, child_name, nesting, parent_optional
            )
            collector.add(
                OutputSpec(
                    name=output_name,
                    value=value,
                    description=child_attr.description,
                    sensitive=child_attr.sensitive,
                ),
                is_set=is_set,
            )


def apply_overrides(spec: OutputSpec, config: GenerationTarget) -> OutputSpec:
    if spec.name not in config.output_tf_overrides:
        return spec
    return spec.apply_override(config.output_tf_overrides[spec.name])


def render_output_block(spec: OutputSpec) -> str:
    lines = [f'output "{spec.name}" {{', f"  value = {spec.value}"]
    if spec.description:
        lines.append(f"  description = {render_description(spec.description)}")
    if spec.sensitive:
        lines.append("  sensitive = true")
    lines.append("}")
    return "\n".join(lines)


def log_set_warnings(collector: OutputCollector, log: logging.Logger) -> None:
    for name in sorted(collector.set_outputs):
        log.warning(
            f"Output '{name}' uses set splat [*] with non-deterministic ordering. "
            f"Consider updating the output description to note this behavior."
        )


def _collect_single_output_entries(
    schema: ResourceSchema,
    config: GenerationTarget,
    indexed_ref: str,
) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """Collect (name, value) entries for single output mode, split by sensitivity."""
    # TODO: Return a typing.NamedTuple instead
    non_sensitive: list[tuple[str, str]] = []
    sensitive: list[tuple[str, str]] = []

    for name, attr in schema.block.attributes.items():
        if not attr.is_output_candidate or name in config.outputs_excluded:
            continue
        entry = (name, f"{indexed_ref}.{name}")
        if attr.sensitive:
            sensitive.append(entry)
        else:
            non_sensitive.append(entry)

    for bt_name, bt in schema.block.block_types.items():
        if bt_name in config.outputs_excluded:
            continue
        has_computed_child = any(
            a.is_output_candidate for a in bt.block.attributes.values()
        )
        if not has_computed_child:
            continue
        has_sensitive_child = any(a.sensitive for a in bt.block.attributes.values())
        entry = (bt_name, f"{indexed_ref}.{bt_name}")
        if has_sensitive_child:
            sensitive.append(entry)
        else:
            non_sensitive.append(entry)

    return sorted(non_sensitive), sorted(sensitive)


def _render_single_output(
    name: str,
    entries: list[tuple[str, str]],
    base_ref: str,
    use_count: bool,
    sensitive: bool = False,
) -> str:
    lines = [f'output "{name}" {{']
    if use_count:
        lines.append(f"  value = length({base_ref}) > 0 ? {{")
        for attr, value in entries:
            lines.append(f"    {attr} = {value}")
        lines.append("  } : null")
    else:
        lines.append("  value = {")
        for attr, value in entries:
            lines.append(f"    {attr} = {value}")
        lines.append("  }")
    if sensitive:
        lines.append("  sensitive = true")
    lines.append("}")
    return "\n".join(lines)


def generate_single_outputs(
    schema: ResourceSchema,
    config: GenerationTarget,
    base_ref: str,
    indexed_ref: str,
) -> str:
    non_sensitive, sensitive = _collect_single_output_entries(
        schema, config, indexed_ref
    )
    output_name = f"{config.outputs_prefix}{config.resource_type}"
    outputs = []

    if non_sensitive:
        outputs.append(
            _render_single_output(
                output_name, non_sensitive, base_ref, config.use_resource_count
            )
        )
    if sensitive:
        outputs.append(
            _render_single_output(
                f"{output_name}_sensitive",
                sensitive,
                base_ref,
                config.use_resource_count,
                sensitive=True,
            )
        )
    return "\n\n".join(outputs)


def generate_multi_outputs(
    schema: ResourceSchema,
    config: GenerationTarget,
    base_ref: str,
    indexed_ref: str,
    log: logging.Logger | None = None,
) -> str:
    collector = OutputCollector(
        base_ref=base_ref, indexed_ref=indexed_ref, config=config
    )
    collect_from_attributes(schema.block.attributes, collector)
    collect_from_block_types(schema.block.block_types, collector)

    specs = [apply_overrides(s, config) for s in collector.outputs]

    # Apply outputs_prefix and count-safe wrapping
    for spec in specs:
        if config.outputs_prefix:
            spec.name = f"{config.outputs_prefix}{spec.name}"
        if config.use_resource_count:
            spec.value = _wrap_count_safe(base_ref, spec.value)

    specs.sort(key=lambda s: s.name)
    if log:
        log_set_warnings(collector, log)

    return render_blocks(specs, render_output_block)


def generate_outputs_tf(
    schema: ResourceSchema,
    config: GenerationTarget,
    provider_name: str,
    log: logging.Logger | None = None,
) -> str:
    base_ref, indexed_ref = build_resource_refs(
        provider_name, config.resource_type, config
    )

    if config.use_single_output:
        return generate_single_outputs(schema, config, base_ref, indexed_ref)

    return generate_multi_outputs(schema, config, base_ref, indexed_ref, log)
