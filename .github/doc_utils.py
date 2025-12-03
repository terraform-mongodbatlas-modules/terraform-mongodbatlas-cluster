"""Shared utilities for documentation generation."""


def _build_warning_text(description: str, regenerate_command: str) -> str:
    """Build the warning text used in generated documentation headers."""
    return (
        f"WARNING: {description} is auto-generated. Do not edit directly.\n"
        "Changes will be overwritten when documentation is regenerated.\n"
        f"Run '{regenerate_command}' to regenerate."
    )


def generate_header_comment(
    description: str,
    regenerate_command: str,
) -> str:
    """
    Generate a standardized header comment for generated documentation.

    Returns HTML comment string with @generated annotation and warning.
    Use this when the comment should be a complete HTML comment block.
    """
    warning_text = _build_warning_text(description, regenerate_command)
    return f"<!-- @generated\n{warning_text}\n-->"


def generate_header_comment_for_section(
    description: str,
    regenerate_command: str,
) -> str:
    """
    Generate header comment for a generated section (without HTML comment wrapper).

    Use this when the comment will be wrapped in HTML comment tags by the caller.
    Returns comment text without HTML comment tags.
    """
    warning_text = _build_warning_text(description, regenerate_command)
    return f"@generated\n{warning_text}"
