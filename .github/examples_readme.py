#!/usr/bin/env python
"""Generate README.md and versions.tf files for examples using terraform-docs config."""

import argparse
import re
from pathlib import Path

import yaml

# Files/folders to skip by default
DEFAULT_SKIP_EXAMPLES = [
    "08_development_cluster",  # Has custom versions.tf and README
    "13_example_import",  # Different structure
]


def load_config(config_path: Path) -> dict:
    """Load the terraform-docs YAML configuration."""
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_template(template_path: Path) -> str:
    """Load the README template."""
    return template_path.read_text(encoding="utf-8")


def get_example_name_from_config(folder_number: int, config: dict) -> str | None:
    """Get example name from config (name + title_suffix if present)."""
    for table in config.get("tables", []):
        for example_row in table.get("example_rows", []):
            if example_row.get("folder") == folder_number:
                name = example_row.get("name", "")
                title_suffix = example_row.get("title_suffix", "")
                if title_suffix:
                    return f"{name} {title_suffix}"
                return name
    return None


def get_example_name(folder_name: str, config: dict) -> str:
    """
    Get example name from config, or extract from folder name as fallback.

    E.g., '01_production_cluster' -> 'Production Cluster'
    """
    # Extract folder number
    match = re.match(r"^(\d+)_", folder_name)
    if match:
        folder_number = int(match.group(1))
        config_name = get_example_name_from_config(folder_number, config)
        if config_name:
            return config_name

    # Fallback: extract from folder name
    name_without_number = re.sub(r"^\d+_", "", folder_name)
    return name_without_number.replace("_", " ").title()


def generate_readme(template: str, example_name: str) -> str:
    """Generate README content by replacing template variables."""
    content = template.replace("{{ .NAME }}", example_name)
    return content


def load_root_versions_tf(root_dir: Path) -> str:
    """Load the root versions.tf file."""
    versions_path = root_dir / "versions.tf"
    return versions_path.read_text(encoding="utf-8")


def generate_versions_tf(base_versions_tf: str, provider_config: str) -> str:
    """Generate versions.tf content by combining base template and provider config."""
    content = base_versions_tf.strip()
    if provider_config:
        content += f"\n\n{provider_config.strip()}"
    content += "\n"
    return content


def find_example_folders(examples_dir: Path) -> list[Path]:
    """Find all example folders (directories starting with numbers)."""
    folders = []
    for item in sorted(examples_dir.iterdir()):
        if item.is_dir() and re.match(r"^\d+_", item.name):
            folders.append(item)
    return folders


def should_skip_example(folder_name: str, skip_list: list[str]) -> bool:
    """Check if example should be skipped."""
    return folder_name in skip_list


def process_example(
    example_dir: Path,
    template: str,
    base_versions_tf: str,
    provider_config: str,
    config: dict,
    dry_run: bool = False,
    skip_readme: bool = False,
    skip_versions: bool = False,
) -> tuple[bool, bool]:
    """
    Process a single example directory.

    Returns:
        Tuple of (readme_generated, versions_generated)
    """
    example_name = get_example_name(example_dir.name, config)

    readme_generated = False
    versions_generated = False

    # Generate README.md
    if not skip_readme:
        readme_path = example_dir / "README.md"
        readme_content = generate_readme(template, example_name)

        if not dry_run:
            readme_path.write_text(readme_content, encoding="utf-8")
        readme_generated = True

    # Generate versions.tf
    if not skip_versions:
        versions_path = example_dir / "versions.tf"
        versions_content = generate_versions_tf(base_versions_tf, provider_config)

        if not dry_run:
            versions_path.write_text(versions_content, encoding="utf-8")
        versions_generated = True

    return readme_generated, versions_generated


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Generate README.md and versions.tf files for examples"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files",
    )
    parser.add_argument(
        "--skip-readme",
        action="store_true",
        help="Skip generating README.md files",
    )
    parser.add_argument(
        "--skip-versions",
        action="store_true",
        help="Skip generating versions.tf files",
    )
    parser.add_argument(
        "--no-skip",
        action="store_true",
        help="Process all examples (don't skip default excluded examples)",
    )

    args = parser.parse_args()

    # Assume script is run from repo root
    root_dir = Path.cwd()
    config_path = root_dir / ".terraform-docs.yml"
    examples_dir = root_dir / "examples"

    # Load configuration
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        return

    config = load_config(config_path)
    examples_readme_config = config.get("examples_readme", {})

    # Get template path
    template_path_str = examples_readme_config.get("readme_template", "")
    if not template_path_str:
        print("Error: readme_template not found in config")
        return

    template_path = root_dir / template_path_str
    if not template_path.exists():
        print(f"Error: Template file not found: {template_path}")
        return

    template = load_template(template_path)

    # Load root versions.tf
    base_versions_tf = load_root_versions_tf(root_dir)

    # Get provider config
    versions_tf_config = examples_readme_config.get("versions_tf", {})
    provider_config = versions_tf_config.get("add", "")

    # Determine skip list
    skip_list = [] if args.no_skip else DEFAULT_SKIP_EXAMPLES

    print("Example README Generator")
    print(f"Template: {template_path_str}")
    if args.dry_run:
        print("Mode: DRY RUN (no files will be modified)")
    if skip_list:
        print(f"Skipping examples: {', '.join(skip_list)}")
    print()

    # Find all example folders
    example_folders = find_example_folders(examples_dir)
    print(f"Found {len(example_folders)} example folders")
    print()

    # Process each example
    total_readme = 0
    total_versions = 0
    total_skipped = 0

    for example_dir in example_folders:
        if should_skip_example(example_dir.name, skip_list):
            total_skipped += 1
            print(f"⊘ {example_dir.name} (skipped)")
            continue

        readme_gen, versions_gen = process_example(
            example_dir,
            template,
            base_versions_tf,
            provider_config,
            config,
            dry_run=args.dry_run,
            skip_readme=args.skip_readme,
            skip_versions=args.skip_versions,
        )

        if readme_gen:
            total_readme += 1
        if versions_gen:
            total_versions += 1

        files = []
        if readme_gen:
            files.append("README.md")
        if versions_gen:
            files.append("versions.tf")

        prefix = "→" if args.dry_run else "✓"
        files_str = ", ".join(files) if files else "no files"
        print(f"{prefix} {example_dir.name} ({files_str})")

    print()
    action = "would be generated" if args.dry_run else "generated"
    print(
        f"Summary: {total_readme} READMEs {action}, {total_versions} versions.tf {action}, {total_skipped} skipped"
    )


if __name__ == "__main__":
    main()
