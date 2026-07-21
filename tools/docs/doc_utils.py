"""Shared utilities for documentation generation."""

from __future__ import annotations

import re

from docs.config_loader import SkipRule

TEMPLATE_VAR_PATTERN = re.compile(r"\{\{\s*\.(?P<var_name>[A-Z_]+)\s*\}\}")
ROOT_CONTEXT_NAME = "root"


def should_skip_template_var(
    context_name: str, var_key: str, skip_rules: list[SkipRule] | None = None
) -> bool:
    """Check if a template variable should be skipped based on context name and skip rules.

    Args:
        context_name: Name used for matching (e.g., example name or "root" for root README).
        var_key: The template variable key (e.g., "production_considerations").
        skip_rules: List of SkipRule objects defining which vars to skip for which contexts.

    Returns:
        True if the variable should be skipped (replaced with empty/removed).
    """
    if not skip_rules:
        return False
    context_name_lower = context_name.lower()
    for rule in skip_rules:
        if rule.context_pattern.lower() in context_name_lower and var_key in rule.skip_vars:
            return True
    return False


def apply_template_vars(
    content: str,
    template_vars: dict[str, str],
    context_name: str = ROOT_CONTEXT_NAME,
    skip_rules: list[SkipRule] | None = None,
) -> str:
    """Replace template variable placeholders with their values.

    Placeholders use the format {{ .VARIABLE_NAME }} (uppercase, with dots).
    If a variable value is empty (or skipped), the entire line containing
    the placeholder is removed.

    Args:
        content: The content containing template variable placeholders.
        template_vars: Dictionary mapping lowercase var names to their values.
        context_name: Name used for skip rule matching (default: "root").
        skip_rules: List of SkipRule objects for skipping variables.

    Returns:
        Content with placeholders replaced (or lines removed for empty values).
    """
    lines = content.split("\n")
    result_lines = []

    for line in lines:
        matches = list(TEMPLATE_VAR_PATTERN.finditer(line))
        if not matches:
            result_lines.append(line)
            continue

        # Check all matches - if any would be empty, skip the entire line
        skip_line = False
        replacements: list[tuple[str, str]] = []

        for match in matches:
            var_name_upper = match.group("var_name")
            var_key = var_name_upper.lower()
            value = template_vars.get(var_key, "")

            if should_skip_template_var(context_name, var_key, skip_rules):
                value = ""

            if not value:
                skip_line = True
                break

            placeholder = f"{{{{ .{var_name_upper} }}}}"
            replacements.append((placeholder, value.rstrip("\n")))

        if skip_line:
            continue

        result_line = line
        for placeholder, value in replacements:
            result_line = result_line.replace(placeholder, value)
        result_lines.append(result_line)

    return "\n".join(result_lines)


def _build_warning_text(description: str, regenerate_command: str) -> str:
    return (
        f"WARNING: {description} is auto-generated. Do not edit directly.\n"
        "Changes will be overwritten when documentation is regenerated.\n"
        f"Run '{regenerate_command}' to regenerate."
    )


def generate_header_comment(description: str, regenerate_command: str) -> str:
    warning_text = _build_warning_text(description, regenerate_command)
    return f"<!-- @generated\n{warning_text}\n-->"


def generate_header_comment_for_section(description: str, regenerate_command: str) -> str:
    warning_text = _build_warning_text(description, regenerate_command)
    return f"@generated\n{warning_text}"
