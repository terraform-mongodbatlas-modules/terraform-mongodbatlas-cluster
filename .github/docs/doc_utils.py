"""Shared utilities for documentation generation."""


def _build_warning_text(description: str, regenerate_command: str) -> str:
    return (
        f"WARNING: {description} is auto-generated. Do not edit directly.\n"
        "Changes will be overwritten when documentation is regenerated.\n"
        f"Run '{regenerate_command}' to regenerate."
    )


def generate_header_comment(description: str, regenerate_command: str) -> str:
    warning_text = _build_warning_text(description, regenerate_command)
    return f"<!-- @generated\n{warning_text}\n-->"


def generate_header_comment_for_section(
    description: str, regenerate_command: str
) -> str:
    warning_text = _build_warning_text(description, regenerate_command)
    return f"@generated\n{warning_text}"
