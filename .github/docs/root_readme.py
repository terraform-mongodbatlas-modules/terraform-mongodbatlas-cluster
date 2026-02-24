"""Generate and update root README.md sections (TOC, TABLES, GETTING_STARTED)."""

import argparse
import re
import sys
from pathlib import Path

from docs import config_loader, doc_utils

GETTING_STARTED_PATTERN = re.compile(
    r"<!-- BEGIN_GETTING_STARTED -->\s*(.*?)\s*<!-- END_GETTING_STARTED -->", re.DOTALL
)


def downgrade_headers(content: str) -> str:
    """Downgrade all headers (## and greater) by one level (e.g., ## -> ###, ### -> ####)."""
    return re.sub(r"^(#{2,})", r"#\1", content, flags=re.MULTILINE)


def extract_getting_started(template_text: str) -> str:
    """Extract content between GETTING_STARTED markers, downgrading ## to ###."""
    match = GETTING_STARTED_PATTERN.search(template_text)
    if not match:
        return ""
    return downgrade_headers(match.group(1).strip()) + "\n"


def find_example_folder(folder_id: str | int, examples_dir: Path) -> str | None:
    """Find example folder by numeric prefix (e.g., 01) or exact name match."""
    for folder in examples_dir.iterdir():
        if not folder.is_dir():
            continue
        # Try numeric prefix match (e.g., "01" -> "01_example_name")
        if isinstance(folder_id, int) or (isinstance(folder_id, str) and folder_id.isdigit()):
            prefix = int(folder_id)
            if folder.name.startswith(f"{prefix:02d}_"):
                return folder.name
        # Try exact name match (e.g., "cloud_provider_access")
        elif folder.name == folder_id:
            return folder.name
    return None


def _resolve_auto_column(auto_config: config_loader.AutoColumnConfig, example_folder: Path) -> str:
    target = example_folder / auto_config.file
    if not target.exists():
        return ""
    content = target.read_text(encoding="utf-8")
    try:
        match = re.search(auto_config.pattern, content)
    except re.error as e:
        raise ValueError(f"invalid auto_column pattern {auto_config.pattern!r}: {e}") from e
    if not match:
        return ""
    if "value" not in match.groupdict():
        raise ValueError(
            f"auto_column pattern {auto_config.pattern!r} must contain a (?P<value>...) named group"
        )
    return match.group("value")


def _display_name(row: config_loader.ExampleRow) -> str:
    if row.title_suffix:
        return f"{row.name} {row.title_suffix}"
    return row.name


def _resolve_column(
    col: str,
    row: config_loader.ExampleRow,
    table_config: config_loader.TableConfig,
    folder_name: str,
    examples_dir: Path,
) -> str:
    if col == table_config.link_column:
        return f"[{_display_name(row)}](./examples/{folder_name})"
    if col == "name":
        return _display_name(row)
    extra = row.model_extra or {}
    value = extra.get(col, "")
    if not value and col in table_config.auto_columns:
        value = _resolve_auto_column(table_config.auto_columns[col], examples_dir / folder_name)
    return value


def generate_toc_from_headings(content: str) -> str:
    toc_lines = []
    heading_pattern = r"^## (.+)$"
    for line in content.split("\n"):
        match = re.match(heading_pattern, line)
        if match:
            heading_text = match.group(1)
            if heading_text.startswith("<!--") or heading_text.startswith("<a name"):
                continue
            anchor = heading_text.lower()
            anchor = re.sub(r"[^\w\s-]", "", anchor)
            anchor = re.sub(r"[\s]+", "-", anchor)
            anchor = anchor.strip("-")
            toc_lines.append(f"- [{heading_text}](#{anchor})")
    return "\n".join(toc_lines)


def generate_tables(tables: list[config_loader.TableConfig], examples_dir: Path) -> str:
    tables_output = []
    for table_config in tables:
        tables_output.append(f"## {table_config.name}\n")
        header = " | ".join(col.replace("_", " ").title() for col in table_config.columns)
        separator = " | ".join("---" for _ in table_config.columns)
        tables_output.append(header)
        tables_output.append(separator)
        for row in table_config.example_rows:
            folder_id = row.folder if row.folder is not None else row.folder_name
            if not folder_id:
                continue
            folder_name = find_example_folder(folder_id, examples_dir)
            if not folder_name:
                continue
            row_data = [
                _resolve_column(col, row, table_config, folder_name, examples_dir)
                for col in table_config.columns
            ]
            tables_output.append(" | ".join(row_data))
        tables_output.append("")
    return "\n".join(tables_output)


def update_section(
    content: str,
    section_name: str,
    new_content: str,
    begin_marker: str,
    end_marker: str,
    header_comment: str | None = None,
) -> str:
    pattern = f"({begin_marker})(.*?)({end_marker})"
    if header_comment:
        replacement = f"\\1\n<!-- {header_comment} -->\n{new_content}\n{end_marker}"
    else:
        replacement = f"\\1\n{new_content}\n{end_marker}"
    new_text = re.sub(pattern, replacement, content, flags=re.DOTALL)
    if new_text == content:
        print(f"Warning: {section_name} markers not found in README.md")
    return new_text


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate and update root README.md TOC and TABLES sections"
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview without modifying")
    parser.add_argument("--skip-toc", action="store_true", help="Skip updating TOC section")
    parser.add_argument("--skip-tables", action="store_true", help="Skip updating TABLES section")
    parser.add_argument(
        "--skip-getting-started",
        action="store_true",
        help="Skip updating GETTING_STARTED section",
    )
    parser.add_argument("--check", action="store_true", help="Check if documentation is up-to-date")
    args = parser.parse_args()

    root_dir = Path.cwd()
    readme_path = root_dir / "README.md"
    examples_dir = root_dir / "examples"

    if not readme_path.exists():
        print(f"Error: README.md not found at {readme_path}")
        return

    original_readme_content = readme_path.read_text(encoding="utf-8")
    readme_content = original_readme_content
    config_dict = config_loader.load_examples_config()
    tables = config_loader.parse_tables_config(config_dict)

    print("Root README.md Generator")
    if args.dry_run:
        print("Mode: DRY RUN (no files will be modified)")
    if args.check:
        print("Mode: CHECK (verifying documentation is up-to-date)")
    print()

    modified = False

    if not args.skip_toc:
        print("Generating TOC from headings...")
        toc_content = generate_toc_from_headings(readme_content)
        readme_content = update_section(
            readme_content,
            "TOC",
            toc_content,
            "<!-- BEGIN_TOC -->",
            "<!-- END_TOC -->",
            doc_utils.generate_header_comment_for_section(
                description="This section",
                regenerate_command="just gen-readme",
            ),
        )
        print("ok TOC generated")
        modified = True

    if not args.skip_tables:
        print("Generating TABLES from config...")
        tables_content = generate_tables(tables, examples_dir)
        readme_content = update_section(
            readme_content,
            "TABLES",
            tables_content,
            "<!-- BEGIN_TABLES -->",
            "<!-- END_TABLES -->",
            doc_utils.generate_header_comment_for_section(
                description="This section",
                regenerate_command="just gen-readme",
            ),
        )
        print("ok TABLES generated")
        modified = True

    if not args.skip_getting_started:
        print("Generating GETTING_STARTED from example template...")
        examples_cfg = config_loader.parse_examples_readme_config(config_dict)
        template_path = root_dir / (examples_cfg.readme_template or "docs/example_readme.md")
        if not template_path.exists():
            print(f"Warning: template not found at {template_path}; skipping GETTING_STARTED")
        else:
            getting_started = extract_getting_started(template_path.read_text(encoding="utf-8"))
            if getting_started:
                getting_started = doc_utils.apply_template_vars(
                    getting_started,
                    examples_cfg.template_vars.vars,
                    context_name="root",
                    skip_rules=examples_cfg.template_vars.skip_rules,
                )
                readme_content = update_section(
                    readme_content,
                    "GETTING_STARTED",
                    getting_started,
                    "<!-- BEGIN_GETTING_STARTED -->",
                    "<!-- END_GETTING_STARTED -->",
                    doc_utils.generate_header_comment_for_section(
                        description="This section",
                        regenerate_command="just gen-readme",
                    ),
                )
                print("ok GETTING_STARTED generated")
                modified = True
            else:
                print("Warning: No GETTING_STARTED markers found in template")

    if args.check:
        if readme_content != original_readme_content:
            print()
            print("ERROR: README.md is out of date!")
            print("Run 'just gen-readme' to update documentation")
            sys.exit(1)
        else:
            print()
            print("ok README.md is up to date")
            return

    if modified and not args.dry_run:
        readme_path.write_text(readme_content, encoding="utf-8")
        print()
        print("README.md updated successfully!")
    elif modified:
        print()
        print("Preview mode - no changes written")
    else:
        print("No updates requested")


if __name__ == "__main__":
    main()
