#!/usr/bin/env python
"""Generate and update root README.md TOC and TABLES sections."""

import argparse
import re
from pathlib import Path

from config_loader import TableConfig, load_examples_config, parse_tables_config
from doc_utils import generate_header_comment_for_section


def find_example_folder(folder_number: int, examples_dir: Path) -> str | None:
    """Find the example folder name by number."""
    for folder in examples_dir.iterdir():
        if folder.is_dir() and folder.name.startswith(f"{folder_number:02d}_"):
            return folder.name
    return None


def extract_cluster_type_from_example(example_folder: Path) -> str:
    """Extract cluster_type from example's main.tf file."""
    main_tf = example_folder / "main.tf"

    if not main_tf.exists():
        return ""

    content = main_tf.read_text(encoding="utf-8")

    # Look for cluster_type = "VALUE" in the main.tf
    match = re.search(r'cluster_type\s*=\s*"([^"]+)"', content)
    if match:
        return match.group(1)

    return ""


def generate_toc_from_headings(content: str) -> str:
    """Generate TOC from markdown headings."""
    toc_lines = []

    # Find all headings (## level)
    heading_pattern = r"^## (.+)$"

    for line in content.split("\n"):
        match = re.match(heading_pattern, line)
        if match:
            heading_text = match.group(1)

            # Skip if it's a comment or special marker
            if heading_text.startswith("<!--") or heading_text.startswith("<a name"):
                continue

            # Create anchor link (lowercase, replace spaces with hyphens)
            anchor = heading_text.lower()
            anchor = re.sub(r"[^\w\s-]", "", anchor)  # Remove special chars
            anchor = re.sub(r"[\s]+", "-", anchor)  # Replace spaces/underscores
            anchor = anchor.strip("-")  # Remove leading/trailing hyphens

            toc_lines.append(f"- [{heading_text}](#{anchor})")

    return "\n".join(toc_lines)


def generate_tables(tables: list[TableConfig], examples_dir: Path) -> str:
    """Generate markdown tables from config."""
    tables_output = []

    for table_config in tables:
        # Add table title
        tables_output.append(f"## {table_config.name}\n")

        # Generate table header
        header = " | ".join(
            col.replace("_", " ").title() for col in table_config.columns
        )
        separator = " | ".join("---" for _ in table_config.columns)
        tables_output.append(header)
        tables_output.append(separator)

        # Generate table rows
        for row in table_config.example_rows:
            folder_name = find_example_folder(row.folder, examples_dir)

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
                elif col == "name":
                    display_name = row.name
                    if row.title_suffix:
                        display_name = f"{display_name} {row.title_suffix}"
                    row_data.append(display_name)
                else:
                    row_data.append("")

            tables_output.append(" | ".join(row_data))

        tables_output.append("")  # Empty line after table

    return "\n".join(tables_output)


def update_section(
    content: str,
    section_name: str,
    new_content: str,
    begin_marker: str,
    end_marker: str,
    header_comment: str | None = None,
) -> str:
    """Update a section between markers in the content."""
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
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Generate and update root README.md TOC and TABLES sections"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files",
    )
    parser.add_argument(
        "--skip-toc",
        action="store_true",
        help="Skip updating TOC section",
    )
    parser.add_argument(
        "--skip-tables",
        action="store_true",
        help="Skip updating TABLES section",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if documentation is up-to-date (exits with code 1 if changes needed)",
    )

    args = parser.parse_args()

    # Paths
    root_dir = Path.cwd()
    readme_path = root_dir / "README.md"
    examples_dir = root_dir / "examples"

    if not readme_path.exists():
        print(f"Error: README.md not found at {readme_path}")
        return

    # Load files
    original_readme_content = readme_path.read_text(encoding="utf-8")
    readme_content = original_readme_content
    config_dict = load_examples_config()
    tables = parse_tables_config(config_dict)

    print("Root README.md Generator")
    if args.dry_run:
        print("Mode: DRY RUN (no files will be modified)")
    if args.check:
        print("Mode: CHECK (verifying documentation is up-to-date)")
    print()

    modified = False

    # Update TOC
    if not args.skip_toc:
        print("Generating TOC from headings...")
        toc_content = generate_toc_from_headings(readme_content)
        readme_content = update_section(
            readme_content,
            "TOC",
            toc_content,
            "<!-- BEGIN_TOC -->",
            "<!-- END_TOC -->",
            generate_header_comment_for_section(
                description="This section",
                regenerate_command="just gen-readme",
            ),
        )
        print("✓ TOC generated")
        modified = True

    # Update TABLES
    if not args.skip_tables:
        print("Generating TABLES from config...")
        tables_content = generate_tables(tables, examples_dir)
        readme_content = update_section(
            readme_content,
            "TABLES",
            tables_content,
            "<!-- BEGIN_TABLES -->",
            "<!-- END_TABLES -->",
            generate_header_comment_for_section(
                description="This section",
                regenerate_command="just gen-readme",
            ),
        )
        print("✓ TABLES generated")
        modified = True

    # Check mode: compare and exit with error if different
    if args.check:
        if readme_content != original_readme_content:
            print()
            print("❌ ERROR: README.md is out of date!")
            print("Run 'just gen-readme' to update documentation")
            import sys

            sys.exit(1)
        else:
            print()
            print("✓ README.md is up to date")
            return

    # Write changes
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
