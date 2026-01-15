"""Generate and update root README.md TOC and TABLES sections."""

import argparse
import re
import sys
from pathlib import Path

from docs import config_loader, doc_utils


def find_example_folder(folder_id: str | int, examples_dir: Path) -> str | None:
    """Find example folder by numeric prefix (e.g., 01) or exact name match."""
    for folder in examples_dir.iterdir():
        if not folder.is_dir():
            continue
        # Try numeric prefix match (e.g., "01" -> "01_example_name")
        if isinstance(folder_id, int) or (
            isinstance(folder_id, str) and folder_id.isdigit()
        ):
            prefix = int(folder_id)
            if folder.name.startswith(f"{prefix:02d}_"):
                return folder.name
        # Try exact name match (e.g., "cloud_provider_access")
        elif folder.name == folder_id:
            return folder.name
    return None


def extract_cluster_type_from_example(example_folder: Path) -> str:
    main_tf = example_folder / "main.tf"
    if not main_tf.exists():
        return ""
    content = main_tf.read_text(encoding="utf-8")
    match = re.search(r'cluster_type\s*=\s*"([^"]+)"', content)
    if match:
        return match.group(1)
    return ""


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
        header = " | ".join(
            col.replace("_", " ").title() for col in table_config.columns
        )
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
            row_data = []
            for col in table_config.columns:
                if col == table_config.link_column:
                    display_name = row.name
                    if row.title_suffix:
                        display_name = f"{display_name} {row.title_suffix}"
                    cell_value = f"[{display_name}](./examples/{folder_name})"
                    row_data.append(cell_value)
                elif col == "cluster_type":
                    cluster_type = row.cluster_type
                    if not cluster_type:
                        example_folder_path = examples_dir / folder_name
                        cluster_type = extract_cluster_type_from_example(
                            example_folder_path
                        )
                    row_data.append(cluster_type)
                elif col == "environment":
                    row_data.append(row.environment)
                elif col == "feature":
                    row_data.append(row.feature)
                elif col == "name":
                    display_name = row.name
                    if row.title_suffix:
                        display_name = f"{display_name} {row.title_suffix}"
                    row_data.append(display_name)
                else:
                    row_data.append("")
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
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview without modifying"
    )
    parser.add_argument(
        "--skip-toc", action="store_true", help="Skip updating TOC section"
    )
    parser.add_argument(
        "--skip-tables", action="store_true", help="Skip updating TABLES section"
    )
    parser.add_argument(
        "--check", action="store_true", help="Check if documentation is up-to-date"
    )
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
