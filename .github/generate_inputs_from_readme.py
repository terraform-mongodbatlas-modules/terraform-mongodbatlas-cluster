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


@dataclass
class Variable:
    name: str
    description: str
    type: str
    default: str
    required: bool


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


def parse_terraform_docs_table(inputs_block: str) -> list[Variable]:
    """
    Parse the standard terraform-docs Inputs markdown table.

    Expects content like:

    ## Inputs
    | Name | Description | Type | Default | Required |
    |------|-------------|------|---------|:--------:|
    | name | ...         | ...  | ...     | yes      |
    """
    lines = [line.rstrip() for line in inputs_block.splitlines()]

    try:
        header_index = next(
            idx
            for idx, line in enumerate(lines)
            if line.strip().lower().startswith("## inputs")
        )
    except StopIteration as exc:
        msg = "Could not find '## Inputs' heading in terraform-docs inputs block."
        raise SystemExit(msg) from exc

    table_lines: list[str] = []
    in_table = False

    for line in lines[header_index + 1 :]:
        if not line.strip():
            if in_table:
                break
            continue

        if line.lstrip().startswith("|"):
            in_table = True
            table_lines.append(line)
        elif in_table:
            break

    if len(table_lines) < 3:
        msg = "Terraform-docs inputs table appears malformed or empty."
        raise SystemExit(msg)

    header = [col.strip().lower() for col in table_lines[0].split("|")[1:-1]]
    expected_header = ["name", "description", "type", "default", "required"]
    if header != expected_header:
        msg = (
            "Unexpected terraform-docs inputs table header. "
            f"Expected '{expected_header}', got '{header}'. "
            "Ensure terraform-docs is using the default markdown table format for Inputs."
        )
        raise SystemExit(msg)

    variables: list[Variable] = []

    for row in table_lines[2:]:
        cells = [col.strip() for col in row.split("|")[1:-1]]
        if len(cells) != 5:
            # Skip rows that do not match the expected shape; this is strict-on-structure but
            # avoids partially parsed variables.
            continue

        name, description, type_, default, required = cells
        variables.append(
            Variable(
                name=name,
                description=description,
                type=type_,
                default=default,
                required=required.lower() == "yes",
            )
        )

    if not variables:
        msg = "No variables were parsed from the terraform-docs inputs table."
        raise SystemExit(msg)

    return variables


def _parse_type_and_default(
    lines: list[str],
    start_index: int,
) -> tuple[str, str, int]:
    type_value = ""
    default_value = ""
    i = start_index

    while i < len(lines):
        stripped = lines[i].strip()
        if stripped.startswith("### ") or stripped.startswith("## "):
            break

        if stripped.startswith("Type:"):
            value = stripped[len("Type:") :].strip()
            i += 1
            if not value and i < len(lines) and lines[i].strip().startswith("```"):
                fence = lines[i].strip()
                fence_prefix = fence[:3]
                i += 1
                code_lines: list[str] = []
                while i < len(lines) and not lines[i].strip().startswith(fence_prefix):
                    code_lines.append(lines[i].rstrip())
                    i += 1
                if i < len(lines) and lines[i].strip().startswith(fence_prefix):
                    i += 1
                value = " ".join(code_lines).strip()
            type_value = value or type_value
            continue

        if stripped.startswith("Default:"):
            value = stripped[len("Default:") :].strip()
            i += 1
            if not value and i < len(lines) and lines[i].strip().startswith("```"):
                fence = lines[i].strip()
                fence_prefix = fence[:3]
                i += 1
                code_lines = []
                while i < len(lines) and not lines[i].strip().startswith(fence_prefix):
                    code_lines.append(lines[i].rstrip())
                    i += 1
                if i < len(lines) and lines[i].strip().startswith(fence_prefix):
                    i += 1
                value = " ".join(code_lines).strip()
            default_value = value or default_value
            continue

        i += 1

    return type_value, default_value, i


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
    lines = [line.rstrip() for line in inputs_block.splitlines()]

    variables: list[Variable] = []
    current_required = False
    i = 0

    while i < len(lines):
        stripped = lines[i].strip()

        if stripped.startswith("## "):
            lower = stripped.lower()
            if "required inputs" in lower:
                current_required = True
            elif "optional inputs" in lower:
                current_required = False
            i += 1
            continue

        if stripped.startswith("### "):
            header_line = lines[i]
            name_match = INPUT_ANCHOR_PATTERN.search(header_line)
            if name_match:
                var_name = name_match.group("var_name")
            else:
                bracket_start = header_line.find("[")
                bracket_end = header_line.find("]", bracket_start + 1)
                var_name = (
                    header_line[bracket_start + 1 : bracket_end]
                    if bracket_start != -1 and bracket_end != -1
                    else header_line.strip("# ").strip()
                )
                var_name = var_name.replace("\\_", "_")

            description_lines: list[str] = []
            i += 1

            while i < len(lines):
                line = lines[i]
                stripped_inner = line.strip()
                if stripped_inner.startswith("### ") or stripped_inner.startswith(
                    "## "
                ):
                    break
                if stripped_inner.startswith("Type:") or stripped_inner.startswith(
                    "Default:"
                ):
                    break
                description_lines.append(line.rstrip())
                i += 1

            type_value, default_value, i = _parse_type_and_default(lines, i)

            description = "\n".join(description_lines).rstrip()
            variables.append(
                Variable(
                    name=var_name,
                    description=description,
                    type=type_value or "",
                    default=default_value or "",
                    required=current_required,
                )
            )
            continue

        i += 1

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
            lines.append(textwrap.dedent(description).strip())
            lines.append("")

        section_vars = grouped.get(title, [])
        if not section_vars:
            lines.append("_No variables in this section yet._")
            lines.append("")
            continue

        variable_heading_level = min(level + 1, 6)

        for var in section_vars:
            lines.append(f"{'#' * variable_heading_level} {var.name}")
            lines.append("")
            if var.description:
                for desc_line in var.description.splitlines():
                    if desc_line.strip():
                        lines.append(desc_line.rstrip())
                lines.append("")

            if var.type:
                lines.append(f"Type: {var.type}")
                lines.append("")

            if var.default:
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

    begin_generated = "<!-- BEGIN_GENERATED_INPUTS -->"
    end_generated = "<!-- END_GENERATED_INPUTS -->"

    begin_index = readme_content.find(begin_generated)
    end_index = readme_content.find(end_generated)

    if begin_index != -1 and end_index != -1:
        end_index += len(end_generated)
        new_block = f"{begin_generated}\n{output_markdown}{end_generated}"
        updated_readme = (
            readme_content[:begin_index] + new_block + readme_content[end_index:]
        )
    else:
        end_inputs_index = readme_content.find(END_MARKER)
        if end_inputs_index == -1:
            msg = (
                "Could not find END_TF_INPUTS_RAW marker in README.md when inserting "
                "generated inputs section."
            )
            raise SystemExit(msg)
        insert_pos = end_inputs_index + len(END_MARKER)
        insertion = f"\n\n{begin_generated}\n{output_markdown}{end_generated}\n"
        updated_readme = (
            readme_content[:insert_pos] + insertion + readme_content[insert_pos:]
        )

    try:
        args.readme.write_text(updated_readme, encoding="utf-8")
    except OSError as exc:
        msg = f"Failed to update README.md with grouped inputs: {exc}"
        raise SystemExit(msg) from exc


if __name__ == "__main__":
    try:
        main()
    except SystemExit as exc:
        sys.stderr.write(str(exc) + "\n")
        raise
