"""Generate grouped inputs markdown from terraform-docs output in README.md."""

import argparse
import re
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path

import yaml

from docs import doc_utils

BEGIN_MARKER = "<!-- BEGIN_TF_INPUTS_RAW -->"
END_MARKER = "<!-- END_TF_INPUTS_RAW -->"
INPUT_ANCHOR_PATTERN = re.compile(r'name="input_(?P<var_name>[^"]+)"')
FENCED_HCL_TYPE_PATTERN = re.compile(
    r"```hcl\s*\n(?P<hcl_content>.*?)\n```",
    re.DOTALL,
)


def avoid_extra_type_indent(type_value: str) -> str:
    match = FENCED_HCL_TYPE_PATTERN.match(type_value)
    if match:
        hcl_body = [line.removeprefix("  ") for line in match.group("hcl_content").splitlines()]
        return "\n".join(["```hcl", *hcl_body, "```"])
    return type_value


def avoid_underscore_escaping(description: str) -> str:
    return description.replace("\\_", "_")


def remove_description_prefix(description: str) -> str:
    return description.removeprefix("\n\nDescription: ")


def _extract_description(text: str) -> str:
    lines = text.split("\n")
    if lines and lines[0].strip().startswith("Description:"):
        first_line = lines[0]
        if first_line.strip() == "Description:":
            lines = lines[1:]
        else:
            desc_content = first_line.split("Description:", 1)[1]
            if desc_content.strip():
                lines[0] = desc_content.strip()
            else:
                lines = lines[1:]
    return "\n".join(lines).rstrip()


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
    block = readme_content[start : end + len(END_MARKER)]
    return block


def parse_terraform_docs_inputs(inputs_block: str) -> list[Variable]:
    section_pattern = re.compile(
        r"^##\s+(Required|Optional)\s+Inputs", re.IGNORECASE | re.MULTILINE
    )
    var_header_pattern = re.compile(
        r"^###\s+<a\s+name=\"input_(?P<var_name>[^\"]+)\"></a>\s+\[(?P<display>[^\]]+)\]\(#input[^\)]+\)",
        re.MULTILINE,
    )
    fenced_block_pattern = re.compile(r"```(\w+)?\n(.*?)\n```", re.MULTILINE | re.DOTALL)
    description_pattern = re.compile(
        r"^(?P<description>.*?)(?=\nType:|\nDefault:|$)", re.MULTILINE | re.DOTALL
    )
    type_pattern = re.compile(
        r"^Type:\s*(?P<type_inline>[^\n]+)(?=\n(?:Default:|###|##|<!--|$))|"
        r"^Type:\s*\n(?P<type_fenced>```\w+\n.*?\n```)(?=\n(?:Default:|###|##|<!--|$))",
        re.MULTILINE | re.DOTALL,
    )
    default_pattern = re.compile(
        r"^Default:\s*(?P<default_inline>[^\n]+)(?=\n(?:###|##|<!--|$))|"
        r"^Default:\s*\n(?P<default_fenced>```\w+\n.*?\n```)(?=\n(?:###|##|<!--|$))",
        re.MULTILINE | re.DOTALL,
    )

    def _extract_fenced_value(fenced_content: str) -> str:
        match = fenced_block_pattern.search(fenced_content)
        if match:
            lang = match.group(1) or "hcl"
            content = match.group(2)
            return f"```{lang}\n{content}\n```"
        return ""

    def _extract_inline_or_fenced(
        var_block: str, pattern: re.Pattern[str], inline_group: str, fenced_group: str
    ) -> str:
        match = pattern.search(var_block)
        if not match:
            return ""
        if match.group(inline_group):
            return match.group(inline_group).strip()
        if match.group(fenced_group):
            return _extract_fenced_value(match.group(fenced_group))
        return ""

    def _parse_description(var_block: str) -> str:
        desc_match = description_pattern.search(var_block)
        if desc_match and desc_match.group("description"):
            return _extract_description(desc_match.group("description"))
        desc_end_match = re.search(r"\n(?:Type:|Default:)", var_block)
        desc_end = desc_end_match.start() if desc_end_match else len(var_block)
        return _extract_description(var_block[:desc_end])

    section_matches = list(section_pattern.finditer(inputs_block))
    if not section_matches:
        section_contents = [(inputs_block, False)]
    else:
        section_contents = []
        for section_idx, section_match in enumerate(section_matches):
            section_start = section_match.end()
            section_end = (
                section_matches[section_idx + 1].start()
                if section_idx + 1 < len(section_matches)
                else len(inputs_block)
            )
            section_content = inputs_block[section_start:section_end]
            is_required = section_match.group(1).lower() == "required"
            section_contents.append((section_content, is_required))

    variables: list[Variable] = []
    for section_content, is_required in section_contents:
        var_matches = list(var_header_pattern.finditer(section_content))
        for var_idx, var_match in enumerate(var_matches):
            var_name = var_match.group("var_name").replace("\\_", "_")
            var_start = var_match.end()
            var_end = (
                var_matches[var_idx + 1].start()
                if var_idx + 1 < len(var_matches)
                else len(section_content)
            )
            var_block = section_content[var_start:var_end]
            description = _parse_description(var_block)
            type_value = _extract_inline_or_fenced(
                var_block, type_pattern, "type_inline", "type_fenced"
            )
            default_value = _extract_inline_or_fenced(
                var_block, default_pattern, "default_inline", "default_fenced"
            )
            variables.append(
                Variable(
                    name=var_name,
                    description=description,
                    type=type_value,
                    default=default_value,
                    required=is_required,
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
        if section.get("is_default"):
            return str(section.get("title", section.get("id", "Other Variables")))
    for section in sections:
        if section.get("id") == "other":
            return str(section.get("title", "Other Variables"))
    return "Other Variables"


def render_grouped_markdown(variables: list[Variable], sections: list[dict[str, object]]) -> str:
    grouped: dict[str, list[Variable]] = {}
    for var in variables:
        section_title = assign_section(var, sections)
        grouped.setdefault(section_title, []).append(var)

    lines: list[str] = []
    header = doc_utils.generate_header_comment(
        description="This grouped inputs section",
        regenerate_command="just docs",
    )
    lines.append(header)

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
            dedented = textwrap.dedent(description).strip()
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
        description="Generate grouped inputs markdown from terraform-docs output in README.md."
    )
    parser.add_argument("--readme", type=Path, default=Path("README.md"), help="Path to README.md")
    parser.add_argument(
        "--config", type=Path, default=Path("docs/inputs_groups.yaml"), help="Groupings config"
    )
    args = parser.parse_args()

    readme_content = load_readme(args.readme)
    inputs_block = extract_inputs_block(readme_content)
    variables = parse_terraform_docs_inputs(inputs_block)
    sections = load_group_config(args.config)
    output_markdown = render_grouped_markdown(variables, sections)
    replacement = f"{BEGIN_MARKER}\n{output_markdown}\n{END_MARKER}"
    new_content = readme_content.replace(inputs_block, replacement)
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
