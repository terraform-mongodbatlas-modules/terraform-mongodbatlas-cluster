"""Generate README.md and versions.tf files for examples using terraform-docs config."""

import argparse
import re
import subprocess
import sys
from pathlib import Path

from docs import config_loader, doc_utils


def load_template(template_path: Path) -> str:
    return template_path.read_text(encoding="utf-8")


def get_example_name_from_config(
    folder_name: str, folder_number: int | None, config: dict
) -> str | None:
    for table in config.get("tables", []):
        for example_row in table.get("example_rows", []):
            # Match by folder_name (string) or folder (numeric prefix)
            if example_row.get("folder_name") == folder_name or (
                folder_number is not None and example_row.get("folder") == folder_number
            ):
                name = example_row.get("name", "")
                title_suffix = example_row.get("title_suffix", "")
                if title_suffix:
                    return f"{name} {title_suffix}"
                return name
    return None


def get_example_name(folder_name: str, config: dict) -> str:
    match = re.match(r"^(\d+)_", folder_name)
    folder_number = int(match.group(1)) if match else None
    config_name = get_example_name_from_config(folder_name, folder_number, config)
    if config_name:
        return config_name
    name_without_number = re.sub(r"^\d+_", "", folder_name)
    return name_without_number.replace("_", " ").title()


def get_registry_source() -> str:
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
    transformed = re.sub(
        r'source\s*=\s*"\.\.\/\.\.\/?"',
        f'source  = "{registry_source}"',
        main_tf_content,
    )
    if version:
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
    header_comment = (
        doc_utils.generate_header_comment(
            description="This file",
            regenerate_command="just gen-examples",
        )
        + "\n"
    )
    content = template.replace("{{ .NAME }}", example_name)
    code_snippet = generate_code_snippet(
        example_dir, registry_source, version, additional_files
    )
    content = content.replace("{{ .CODE_SNIPPET }}", code_snippet)
    for key, value in sorted(template_vars.items()):
        if should_skip_template_var(example_name, key, skip_var_patterns):
            value = ""
        content = content.replace(f"{{{{ .{key.upper()} }}}}", value.rstrip("\n"))
    lines = content.split("\n")
    if lines and lines[0].strip().startswith("<!--") and "used to generate" in lines[0]:
        content = "\n".join(lines[1:])
    return header_comment + content


def load_root_versions_tf(root_dir: Path) -> str:
    versions_path = root_dir / "versions.tf"
    return versions_path.read_text(encoding="utf-8")


def generate_versions_tf(base_versions_tf: str, provider_config: str) -> str:
    content = base_versions_tf.strip()
    if provider_config:
        content += f"\n\n{provider_config.strip()}"
    content += "\n"
    return content


def find_example_folders(examples_dir: Path) -> list[Path]:
    """Find example folders - supports both numeric prefixes (01_name) and plain names."""
    folders = []
    for item in sorted(examples_dir.iterdir()):
        if item.is_dir() and (item / "main.tf").exists():
            folders.append(item)

    # Sort: numeric-prefixed first (by number), then alphabetically
    def sort_key(p: Path) -> tuple[int, int, str]:
        match = re.match(r"^(\d+)_", p.name)
        if match:
            return (0, int(match.group(1)), p.name)
        return (1, 0, p.name)

    return sorted(folders, key=sort_key)


def should_skip_example(folder_name: str, skip_list: list[str] | None) -> bool:
    if not skip_list:
        return False
    return folder_name in skip_list


def should_generate_versions_tf(
    example_name: str,
    example_dir: Path,
    versions_tf_config: config_loader.VersionsTfConfig,
) -> bool:
    if versions_tf_config.force_generate:
        return True
    versions_path = example_dir / "versions.tf"
    if not versions_path.exists():
        return True
    if versions_tf_config.skip_if_name_contains:
        example_name_lower = example_name.lower()
        for pattern in versions_tf_config.skip_if_name_contains:
            if pattern.lower() in example_name_lower:
                return False
    return not versions_tf_config.generate_when_missing_only


def process_example(
    example_dir: Path,
    template: str,
    base_versions_tf: str,
    config: dict,
    registry_source: str,
    examples_readme_config: config_loader.ExamplesReadmeConfig,
    version: str | None = None,
    dry_run: bool = False,
    skip_readme: bool = False,
    skip_versions: bool = False,
    check: bool = False,
) -> tuple[bool, bool, bool]:
    example_name = get_example_name(example_dir.name, config)
    readme_generated = False
    versions_generated = False
    has_changes = False
    if not skip_readme:
        readme_path = example_dir / "README.md"
        readme_content = generate_readme(
            template,
            example_name,
            example_dir,
            registry_source,
            examples_readme_config.template_vars.vars,
            version,
            examples_readme_config.code_snippet_files.additional,
            examples_readme_config.template_vars.skip_if_name_contains,
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
        if should_generate_versions_tf(
            example_name, example_dir, examples_readme_config.versions_tf
        ):
            versions_path = example_dir / "versions.tf"
            versions_content = generate_versions_tf(
                base_versions_tf, examples_readme_config.versions_tf.add
            )
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
    parser = argparse.ArgumentParser(
        description="Generate README.md and versions.tf files for examples"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without modifying"
    )
    parser.add_argument(
        "--skip-readme", action="store_true", help="Skip generating README.md"
    )
    parser.add_argument(
        "--skip-versions", action="store_true", help="Skip generating versions.tf"
    )
    parser.add_argument("--no-skip", action="store_true", help="Process all examples")
    parser.add_argument(
        "--check", action="store_true", help="Check if documentation is up-to-date"
    )
    parser.add_argument(
        "--version", type=str, default=None, help="Module version for code snippets"
    )
    args = parser.parse_args()

    root_dir = Path.cwd()
    examples_dir = root_dir / "examples"
    config = config_loader.load_examples_config()
    examples_readme_config = config_loader.parse_examples_readme_config(config)

    if not examples_readme_config.readme_template:
        print("Error: readme_template not found in config")
        sys.exit(1)

    template_path = root_dir / examples_readme_config.readme_template
    if not template_path.exists():
        print(f"Error: Template file not found: {template_path}")
        sys.exit(1)

    template = load_template(template_path)
    base_versions_tf = load_root_versions_tf(root_dir)
    skip_list: list[str] | None = (
        None if args.no_skip else examples_readme_config.skip_examples
    )

    try:
        registry_source = get_registry_source()
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to get registry source: {e}", file=sys.stderr)
        sys.exit(1)

    print("Example README Generator")
    print(f"Template: {examples_readme_config.readme_template}")
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

    example_folders = find_example_folders(examples_dir)
    print(f"Found {len(example_folders)} example folders")
    print()

    total_readme = 0
    total_versions = 0
    total_skipped = 0
    examples_with_changes = []

    for example_dir in example_folders:
        if should_skip_example(example_dir.name, skip_list):
            total_skipped += 1
            print(f"- {example_dir.name} (skipped)")
            continue
        readme_gen, versions_gen, has_changes = process_example(
            example_dir,
            template,
            base_versions_tf,
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
            prefix = "x" if has_changes else "ok"
        else:
            prefix = "->" if args.dry_run else "ok"
        files_str = ", ".join(files) if files else "no files"
        print(f"{prefix} {example_dir.name} ({files_str})")

    print()
    if args.check:
        if examples_with_changes:
            print(
                f"ERROR: {len(examples_with_changes)} example(s) have outdated documentation:"
            )
            for example_name in examples_with_changes:
                print(f"  - {example_name}")
            print()
            print("Run 'just gen-examples' to update documentation")
            sys.exit(1)
        else:
            print("All example documentation is up to date")
    else:
        action = "would be generated" if args.dry_run else "generated"
        print(
            f"Summary: {total_readme} READMEs {action}, {total_versions} versions.tf {action}"
        )
        print(f"  {total_skipped} skipped")


if __name__ == "__main__":
    main()
