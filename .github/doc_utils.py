"""Shared utilities for documentation generation."""


def generate_header_comment(
    description: str,
    regenerate_command: str,
) -> str:
    """
    Generate a standardized header comment for generated documentation.

    Returns HTML comment string with @generated annotation and warning.
    Use this when the comment should be a complete HTML comment block.
    """
    warning_text = (
        f"WARNING: {description} is auto-generated. Do not edit directly.\n"
        "Changes will be overwritten when documentation is regenerated.\n"
        f"Run '{regenerate_command}' to regenerate."
    )

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
    warning_text = (
        f"@generated\n"
        f"WARNING: {description} is auto-generated. Do not edit directly.\n"
        "Changes will be overwritten when documentation is regenerated.\n"
        f"Run '{regenerate_command}' to regenerate."
    )

    return warning_text
