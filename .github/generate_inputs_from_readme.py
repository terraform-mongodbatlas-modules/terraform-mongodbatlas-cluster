from __future__ import annotations

import argparse
import re
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path

import yaml

BEGIN_MARKER = "<!-- BEGIN_TF_INPUTS_RAW"
END_MARKER = "END_TF_INPUTS_RAW -->"
INPUT_ANCHOR_PATTERN = re.compile(r'name="input_(?P<var_name>[^"]+)"')
FENCED_HCL_TYPE_PATTERN = re.compile(
    r"```hcl\s*\n"
    r"(?P<hcl_content>.*?)"
    r"\n```",
    re.DOTALL,  # Makes . match newlines so multi-line HCL content is captured
)


def avoid_extra_type_indent(type_value: str) -> str:
    match = FENCED_HCL_TYPE_PATTERN.match(type_value)
    if match:
        hcl_body = [
            line.removeprefix("  ") for line in match.group("hcl_content").splitlines()
        ]
        return "\n".join(
            [
                "```hcl",
                *hcl_body,
                "```",
            ]
        )

    return type_value


def avoid_underscore_escaping(description: str) -> str:
    return description.replace("\\_", "_")


def remove_description_prefix(description: str) -> str:
    return description.removeprefix("\n\nDescription: ")

@dataclass
class Variable:
    name: str
    description: str
    type: str
    default: str
    required: bool

    def __post_init__(self) -> None:
        self.type = avoid_extra_type_indent(self.type)
        self.description = avoid_underscore_escaping(self.description)
        self.description = remove_description_prefix(self.description)


def load_readme(readme_path: Path) -> str:
    try:
        return readme_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        msg = f"README file not found at {readme_path}"
        raise SystemExit(msg) from exc


def extract_inputs_block(readme_content: str) -> str:
    start = readme_content.find(BEGIN_MARKER)
    end = readme_content.find(END_MARKER)

    if start == -1 or end == -1 or end <= start:
        msg = (
            "Could not find terraform-docs inputs block in README.md. "
            f"Expected markers '{BEGIN_MARKER}' ... '{END_MARKER}'. "
            "Ensure terraform-docs has been run with the updated .terraform-docs.yml."
        )
        raise SystemExit(msg)

    block = readme_content[start:end]
    return block


def parse_terraform_docs_inputs(inputs_block: str) -> list[Variable]:
    """
    Parse the terraform-docs markdown used in this repository, which structures inputs as:

    ## Required Inputs
    ...
    ### <a name="input_name"></a> [name](#input_name)
    Description: ...
    Type: `string`

    ## Optional Inputs
    ...
    ### <a name="input_other"></a> [other](#input_other)
    Description: ...
    Type: ...
    Default: ...
    """
    # Pattern to match section headers
    section_pattern = re.compile(
        r"^##\s+(Required|Optional)\s+Inputs", re.IGNORECASE | re.MULTILINE
    )

    # Pattern to match variable header: ### <a name="input_name"></a> [name](#input_name)
    # Handles escaped underscores in the link like #input\_regions
    var_header_pattern = re.compile(
        r"^###\s+<a\s+name=\"input_(?P<var_name>[^\"]+)\"></a>\s+\[(?P<display>[^\]]+)\]\(#input[^\)]+\)",
        re.MULTILINE,
    )

    # Pattern to match fenced code blocks (```lang\n...\n```)
    fenced_block_pattern = re.compile(
        r"```(\w+)?\n(.*?)\n```", re.MULTILINE | re.DOTALL
    )

    # Separate regex patterns for each section with named groups
    # Pattern to match description: everything until Type: or Default:
    # Uses non-greedy match to stop at first Type: or Default:
    description_pattern = re.compile(
        r"^(?P<description>.*?)(?=\nType:|\nDefault:|$)", re.MULTILINE | re.DOTALL
    )

    # Pattern to match Type section: Type: followed by inline value or fenced block
    # Handles both "Type: `string`" (inline) and "Type:\n\n```hcl\n...\n```" (fenced)
    type_pattern = re.compile(
        r"^Type:\s*(?P<type_inline>[^\n]+)(?=\n(?:Default:|###|##|$))|"
        r"^Type:\s*\n(?P<type_fenced>```\w+\n.*?\n```)(?=\n(?:Default:|###|##|$))",
        re.MULTILINE | re.DOTALL,
    )

    # Pattern to match Default section: Default: followed by inline value or fenced block
    # Handles both "Default: `null`" (inline) and "Default:\n\n```hcl\n...\n```" (fenced)
    default_pattern = re.compile(
        r"^Default:\s*(?P<default_inline>[^\n]+)(?=\n(?:###|##|$))|"
        r"^Default:\s*\n(?P<default_fenced>```\w+\n.*?\n```)(?=\n(?:###|##|$))",
        re.MULTILINE | re.DOTALL,
    )

    variables: list[Variable] = []

    # Find all section boundaries
    section_matches = list(section_pattern.finditer(inputs_block))

    # If no sections found, treat entire block as optional
    if not section_matches:
        section_matches = [None]  # Dummy entry to process once
        section_contents = [(inputs_block, False)]
    else:
        section_contents = []
        for section_idx, section_match in enumerate(section_matches):
            section_type = section_match.group(1)
            section_start = section_match.end()
            section_end = (
                section_matches[section_idx + 1].start()
                if section_idx + 1 < len(section_matches)
                else len(inputs_block)
            )
            section_content = inputs_block[section_start:section_end]
            current_required = section_type.lower() == "required"
            section_contents.append((section_content, current_required))

    # Process each section
    for section_content, current_required in section_contents:
        # Find all variable headers in this section
        var_matches = list(var_header_pattern.finditer(section_content))
        if not var_matches:
            continue

        for var_idx, var_match in enumerate(var_matches):
            var_name = var_match.group("var_name").replace("\\_", "_")
            var_start = var_match.end()

            # Find the end of this variable block (start of next variable or section)
            var_end = (
                var_matches[var_idx + 1].start()
                if var_idx + 1 < len(var_matches)
                else len(section_content)
            )
            var_block = section_content[var_start:var_end]

            # Extract description using named group pattern
            description = ""
            desc_match = description_pattern.search(var_block)
            if desc_match and desc_match.group("description"):
                description_text = desc_match.group("description")
                # Remove "Description: " prefix if present, preserving blank lines
                description_lines = description_text.split("\n")
                if description_lines and description_lines[0].strip().startswith(
                    "Description:"
                ):
                    first_line = description_lines[0]
                    if first_line.strip() == "Description:":
                        description_lines = description_lines[1:]
                    else:
                        desc_content = first_line.split("Description:", 1)[1]
                        if desc_content.strip():
                            description_lines[0] = desc_content.strip()
                        else:
                            description_lines = description_lines[1:]
                description = "\n".join(description_lines).rstrip()
            else:
                # Fallback: find description manually
                desc_end_match = re.search(r"\n(?:Type:|Default:)", var_block)
                desc_end = desc_end_match.start() if desc_end_match else len(var_block)
                description_text = var_block[:desc_end]
                description_lines = description_text.split("\n")
                if description_lines and description_lines[0].strip().startswith(
                    "Description:"
                ):
                    first_line = description_lines[0]
                    if first_line.strip() == "Description:":
                        description_lines = description_lines[1:]
                    else:
                        desc_content = first_line.split("Description:", 1)[1]
                        if desc_content.strip():
                            description_lines[0] = desc_content.strip()
                        else:
                            description_lines = description_lines[1:]
                description = "\n".join(description_lines).rstrip()

            # Extract type using named group pattern
            type_value = ""
            type_match = type_pattern.search(var_block)
            if type_match:
                if type_match.group("type_inline"):
                    type_value = type_match.group("type_inline").strip()
                elif type_match.group("type_fenced"):
                    fenced_content = type_match.group("type_fenced")
                    fenced_match = fenced_block_pattern.search(fenced_content)
                    if fenced_match:
                        lang = fenced_match.group(1) or "hcl"
                        content = fenced_match.group(2)
                        type_value = f"```{lang}\n{content}\n```"

            # Extract default using named group pattern
            default_value = ""
            default_match = default_pattern.search(var_block)
            if default_match:
                if default_match.group("default_inline"):
                    default_value = default_match.group("default_inline").strip()
                elif default_match.group("default_fenced"):
                    fenced_content = default_match.group("default_fenced")
                    fenced_match = fenced_block_pattern.search(fenced_content)
                    if fenced_match:
                        lang = fenced_match.group(1) or "hcl"
                        content = fenced_match.group(2)
                        default_value = f"```{lang}\n{content}\n```"

            variables.append(
                Variable(
                    name=var_name,
                    description=description,
                    type=type_value,
                    default=default_value,
                    required=current_required,
                )
            )

    if not variables:
        msg = "No variables were parsed from the terraform-docs inputs section."
        raise SystemExit(msg)

    return variables


def load_group_config(config_path: Path) -> list[dict[str, object]]:
    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        msg = f"Inputs grouping config not found at {config_path}"
        raise SystemExit(msg) from exc

    if not isinstance(raw, dict) or "sections" not in raw:
        msg = f"Invalid grouping config in {config_path}: expected a 'sections' key."
        raise SystemExit(msg)

    sections = raw["sections"]
    if not isinstance(sections, list):
        msg = f"Invalid grouping config in {config_path}: 'sections' must be a list."
        raise SystemExit(msg)

    return sections


def assign_section(variable: Variable, sections: list[dict[str, object]]) -> str:
    for section in sections:
        match = section.get("match", {}) or {}
        names = match.get("names", [])
        if isinstance(names, list) and variable.name in names:
            return str(section.get("title", section.get("id", "Other")))

    for section in sections:
        match = section.get("match", {}) or {}
        if match.get("required") and variable.required:
            return str(section.get("title", section.get("id", "Required Variables")))

    for section in sections:
        if section.get("id") == "other":
            return str(section.get("title", "Other Variables"))

    return "Other Variables"


def render_grouped_markdown(
    variables: list[Variable],
    sections: list[dict[str, object]],
) -> str:
    grouped: dict[str, list[Variable]] = {}

    for var in variables:
        section_title = assign_section(var, sections)
        grouped.setdefault(section_title, []).append(var)

    lines: list[str] = []

    for section in sections:
        title = str(section.get("title", section.get("id", "Variables")))
        level_raw = section.get("level", 2)
        try:
            level = int(level_raw)
        except (TypeError, ValueError):
            level = 2
        level = min(max(level, 1), 6)
        description = section.get("description")

        lines.append(f"{'#' * level} {title}")
        lines.append("")

        if isinstance(description, str) and description.strip():
            # Handle multi-line descriptions - preserve formatting
            # YAML multi-line strings often have leading whitespace that should be dedented
            dedented = textwrap.dedent(description).strip()
            # Preserve line breaks and formatting
            for desc_line in dedented.splitlines():
                lines.append(desc_line.rstrip())
            lines.append("")

        section_vars = grouped.get(title, [])
        if not section_vars:
            lines.append("_No variables in this section yet._")
            lines.append("")
            continue

        match = section.get("match", {}) or {}
        names_order = match.get("names", [])
        if isinstance(names_order, list) and names_order:
            vars_by_name: dict[str, Variable] = {v.name: v for v in section_vars}
            ordered_vars: list[Variable] = []
            for name in names_order:
                var = vars_by_name.pop(name, None)
                if var is not None:
                    ordered_vars.append(var)
            for var in section_vars:
                if var.name in vars_by_name:
                    ordered_vars.append(var)
            section_vars = ordered_vars

        variable_heading_level = min(level + 1, 6)

        for var in section_vars:
            lines.append(f"{'#' * variable_heading_level} {var.name}")
            lines.append("")
            if var.description:
                for desc_line in var.description.splitlines():
                    lines.append(desc_line.rstrip())
                lines.append("")

            if var.type:
                if "```" in var.type or "\n" in var.type:
                    lines.append("Type:")
                    lines.append("")
                    lines.append(var.type)
                else:
                    lines.append(f"Type: {var.type}")
                lines.append("")

            if var.default:
                if "```" in var.default or "\n" in var.default:
                    lines.append("Default:")
                    lines.append("")
                    lines.append(var.default)
                else:
                    lines.append(f"Default: {var.default}")
                lines.append("")

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a grouped inputs markdown file from terraform-docs output embedded "
            "in README.md."
        )
    )
    parser.add_argument(
        "--readme",
        type=Path,
        default=Path("README.md"),
        help="Path to README.md containing the terraform-docs inputs block.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("docs/inputs_groups.yaml"),
        help="Path to YAML config describing variable groupings.",
    )
    args = parser.parse_args()

    readme_content = load_readme(args.readme)
    inputs_block = extract_inputs_block(readme_content)
    variables = parse_terraform_docs_inputs(inputs_block)
    sections = load_group_config(args.config)
    output_markdown = render_grouped_markdown(variables, sections)
    new_content = readme_content.replace(inputs_block, output_markdown)
    try:
        args.readme.write_text(new_content, encoding="utf-8")
    except OSError as exc:
        msg = f"Failed to update README.md with grouped inputs: {exc}"
        raise SystemExit(msg) from exc


if __name__ == "__main__":
    try:
        main()
    except SystemExit as exc:
        sys.stderr.write(str(exc) + "\n")
        raise
