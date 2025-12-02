#!/usr/bin/env python
"""Generate README.md and versions.tf files for examples using terraform-docs config."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import yaml


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


def get_registry_source() -> str:
    """Get Terraform Registry source by calling justfile command."""
    result = subprocess.run(
        ["just", "tf-registry-source"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def get_example_terraform_files(
    example_dir: Path, additional_files: list[str] | None = None
) -> tuple[str, dict[str, str], list[str]]:
    """
    Get Terraform files in example directory.

    Returns:
        Tuple of (main_tf_content, additional_file_contents, other_file_names)
    """
    main_tf = example_dir / "main.tf"
    main_content = main_tf.read_text(encoding="utf-8") if main_tf.exists() else ""

    additional_contents: dict[str, str] = {}
    if additional_files:
        for filename in additional_files:
            file_path = example_dir / filename
            if file_path.exists():
                additional_contents[filename] = file_path.read_text(encoding="utf-8")

    other_files = [
        f.name
        for f in sorted(example_dir.glob("*.tf"))
        if f.name != "main.tf" and f.name not in (additional_files or [])
    ]

    return main_content, additional_contents, other_files


def transform_main_tf_for_registry(
    main_tf_content: str, registry_source: str, version: str | None = None
) -> str:
    """
    Transform main.tf to use registry source instead of local path.

    Replaces:
        source = "../.."
    With:
        source  = "registry_source"
        version = "version"  # if version provided
    """
    # Replace source = "../.." with registry source
    transformed = re.sub(
        r'source\s*=\s*"\.\.\/\.\."',
        f'source  = "{registry_source}"',
        main_tf_content,
    )

    # Add version after source if provided
    if version:
        # Find the source line and add version after it
        transformed = re.sub(
            rf'(source\s*=\s*"{re.escape(registry_source)}")',
            rf'\1\n  version = "{version}"',
            transformed,
        )

    return transformed


def generate_code_snippet(
    example_dir: Path,
    registry_source: str,
    version: str | None = None,
    additional_files: list[str] | None = None,
) -> str:
    """Generate code snippet section for README."""
    main_tf, additional_contents, other_files = get_example_terraform_files(
        example_dir, additional_files
    )
    if not main_tf:
        return ""

    transformed_main = transform_main_tf_for_registry(main_tf, registry_source, version)

    snippet = "## Code Snippet\n\n"
    snippet += "Copy and use this code to get started quickly:\n\n"
    snippet += "**main.tf**\n"
    snippet += "```hcl\n"
    snippet += transformed_main
    snippet += "```\n\n"

    for filename, content in sorted(additional_contents.items()):
        transformed_content = transform_main_tf_for_registry(
            content, registry_source, version
        )
        snippet += f"**{filename}**\n"
        snippet += "```hcl\n"
        snippet += transformed_content
        snippet += "```\n\n"

    if other_files:
        snippet += "**Additional files needed:**\n"
        for filename in sorted(other_files):
            snippet += f"- [{filename}](./{filename})\n"
        snippet += "\n"

    return snippet


def should_skip_template_var(
    example_name: str, var_key: str, skip_patterns: list[str] | None = None
) -> bool:
    """Check if a template variable should be skipped for this example."""
    if not skip_patterns:
        return False
    example_name_lower = example_name.lower()
    for pattern in skip_patterns:
        if pattern.lower() in example_name_lower and var_key.startswith("production"):
            return True
    return False


def generate_readme(
    template: str,
    example_name: str,
    example_dir: Path,
    registry_source: str,
    template_vars: dict[str, str],
    version: str | None = None,
    additional_files: list[str] | None = None,
    skip_var_patterns: list[str] | None = None,
) -> str:
    """Generate README content by replacing template variables."""
    content = template.replace("{{ .NAME }}", example_name)

    code_snippet = generate_code_snippet(
        example_dir, registry_source, version, additional_files
    )
    content = content.replace("{{ .CODE_SNIPPET }}", code_snippet)

    for key, value in sorted(template_vars.items()):
        if should_skip_template_var(example_name, key, skip_var_patterns):
            value = ""
        content = content.replace(f"{{{{ .{key.upper()} }}}}", value.rstrip("\n"))

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


def should_skip_example(folder_name: str, skip_list: list[str] | None) -> bool:
    """Check if example should be skipped."""
    if not skip_list:
        return False
    return folder_name in skip_list


def should_generate_versions_tf(
    example_name: str,
    example_dir: Path,
    versions_tf_config: dict,
    force_generate: bool = False,
) -> bool:
    """Determine if versions.tf should be generated for this example."""
    if force_generate:
        return True

    versions_path = example_dir / "versions.tf"
    if not versions_path.exists():
        return True

    skip_patterns = versions_tf_config.get("skip_if_name_contains", [])
    if skip_patterns:
        example_name_lower = example_name.lower()
        for pattern in skip_patterns:
            if pattern.lower() in example_name_lower:
                return False

    return versions_tf_config.get("generate_when_missing_only", False) is False


def process_example(
    example_dir: Path,
    template: str,
    template_vars: dict[str, str],
    base_versions_tf: str,
    provider_config: str,
    config: dict,
    registry_source: str,
    examples_readme_config: dict,
    version: str | None = None,
    dry_run: bool = False,
    skip_readme: bool = False,
    skip_versions: bool = False,
    check: bool = False,
) -> tuple[bool, bool, bool]:
    """
    Process a single example directory.

    Returns:
        Tuple of (readme_generated, versions_generated, has_changes)
    """
    example_name = get_example_name(example_dir.name, config)

    readme_generated = False
    versions_generated = False
    has_changes = False

    if not skip_readme:
        readme_path = example_dir / "README.md"
        additional_files = examples_readme_config.get("code_snippet_files", {}).get(
            "additional", []
        )
        skip_var_patterns = examples_readme_config.get("template_vars", {}).get(
            "skip_if_name_contains", []
        )
        readme_content = generate_readme(
            template,
            example_name,
            example_dir,
            registry_source,
            template_vars,
            version,
            additional_files,
            skip_var_patterns,
        )

        if check and readme_path.exists():
            existing_content = readme_path.read_text(encoding="utf-8")
            if existing_content != readme_content:
                has_changes = True
        elif check:
            has_changes = True

        if not dry_run and not check:
            readme_path.write_text(readme_content, encoding="utf-8")
        readme_generated = True

    if not skip_versions:
        versions_tf_config = examples_readme_config.get("versions_tf", {})
        force_generate = versions_tf_config.get("force_generate", False)
        if should_generate_versions_tf(
            example_name, example_dir, versions_tf_config, force_generate
        ):
            versions_path = example_dir / "versions.tf"
            versions_content = generate_versions_tf(base_versions_tf, provider_config)

            if check and versions_path.exists():
                existing_content = versions_path.read_text(encoding="utf-8")
                if existing_content != versions_content:
                    has_changes = True
            elif check:
                has_changes = True

            if not dry_run and not check:
                versions_path.write_text(versions_content, encoding="utf-8")
            versions_generated = True

    return readme_generated, versions_generated, has_changes


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
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if documentation is up-to-date (exits with code 1 if changes needed)",
    )
    parser.add_argument(
        "--version",
        type=str,
        default=None,
        help="Module version to include in code snippets (e.g., v1.0.0) empty for latest",
    )

    args = parser.parse_args()

    # Assume script is run from repo root
    root_dir = Path.cwd()
    config_path = root_dir / ".terraform-docs.yml"
    examples_dir = root_dir / "examples"

    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)

    config = load_config(config_path)
    examples_readme_config = config.get("examples_readme", {})

    template_vars_raw = examples_readme_config.get("template_vars", {})
    template_vars = {
        k: v for k, v in template_vars_raw.items() if not k.startswith("skip_")
    }

    template_path_str = examples_readme_config.get("readme_template", "")
    if not template_path_str:
        print("Error: readme_template not found in config")
        sys.exit(1)

    template_path = root_dir / template_path_str
    if not template_path.exists():
        print(f"Error: Template file not found: {template_path}")
        sys.exit(1)

    template = load_template(template_path)

    base_versions_tf = load_root_versions_tf(root_dir)

    versions_tf_config = examples_readme_config.get("versions_tf", {})
    provider_config = versions_tf_config.get("add", "")

    skip_list: list[str] | None = None
    if not args.no_skip:
        skip_list = examples_readme_config.get("skip_examples", [])

    try:
        registry_source = get_registry_source()
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to get registry source: {e}", file=sys.stderr)
        sys.exit(1)

    print("Example README Generator")
    print(f"Template: {template_path_str}")
    print(f"Registry source: {registry_source}")
    if args.version:
        print(f"Version: {args.version}")
    if args.dry_run:
        print("Mode: DRY RUN (no files will be modified)")
    if args.check:
        print("Mode: CHECK (verifying documentation is up-to-date)")
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
    examples_with_changes = []

    for example_dir in example_folders:
        if should_skip_example(example_dir.name, skip_list):
            total_skipped += 1
            print(f"⊘ {example_dir.name} (skipped)")
            continue

        readme_gen, versions_gen, has_changes = process_example(
            example_dir,
            template,
            template_vars,
            base_versions_tf,
            provider_config,
            config,
            registry_source,
            examples_readme_config,
            version=args.version,
            dry_run=args.dry_run,
            skip_readme=args.skip_readme,
            skip_versions=args.skip_versions,
            check=args.check,
        )

        if readme_gen:
            total_readme += 1
        if versions_gen:
            total_versions += 1
        if has_changes:
            examples_with_changes.append(example_dir.name)

        files = []
        if readme_gen:
            files.append("README.md")
        if versions_gen:
            files.append("versions.tf")

        if args.check:
            prefix = "❌" if has_changes else "✓"
        else:
            prefix = "→" if args.dry_run else "✓"
        files_str = ", ".join(files) if files else "no files"
        print(f"{prefix} {example_dir.name} ({files_str})")

    print()

    # Check mode: exit with error if any changes detected
    if args.check:
        if examples_with_changes:
            print(
                f"❌ ERROR: {len(examples_with_changes)} example(s) have outdated documentation:"
            )
            for example_name in examples_with_changes:
                print(f"  - {example_name}")
            print()
            print("Run 'just gen-examples' to update documentation")
            sys.exit(1)
        else:
            print("✓ All example documentation is up to date")
    else:
        action = "would be generated" if args.dry_run else "generated"
        print(
            f"Summary: {total_readme} READMEs {action}, {total_versions} versions.tf {action}, {total_skipped} skipped"
        )


if __name__ == "__main__":
    main()
