"""Update module_version in versions.tf file and add provider_meta if missing."""

import re
import sys
from pathlib import Path

MONGODBATLAS_PROVIDER_PATTERN = r'source\s*=\s*"mongodb/mongodbatlas"'
PROVIDER_META_PATTERN = r'provider_meta\s+"mongodbatlas"'
MODULE_NAME_PATTERN = r'module_name\s*=\s*"([^"]*)"'
MODULE_VERSION_PATTERN = r'module_version\s*=\s*"[^"]*"'


def extract_version_number(version: str) -> str:
    if version.startswith("v"):
        return version[1:]
    return version


def get_module_name_from_root(repo_root: Path) -> str | None:
    """Extract module_name from root versions.tf."""
    root_versions = repo_root / "versions.tf"
    if not root_versions.exists():
        return None
    content = root_versions.read_text(encoding="utf-8")
    match = re.search(MODULE_NAME_PATTERN, content)
    return match.group(1) if match else None


def has_mongodbatlas_provider(content: str) -> bool:
    """Check if file uses mongodbatlas provider."""
    return bool(re.search(MONGODBATLAS_PROVIDER_PATTERN, content))


def has_provider_meta(content: str) -> bool:
    """Check if file already has provider_meta block."""
    return bool(re.search(PROVIDER_META_PATTERN, content))


def inject_provider_meta(content: str, module_name: str, version: str) -> str | None:
    """Inject provider_meta block inside the terraform block, before its closing brace.

    Returns the updated content, or None if injection failed (e.g., no terraform block found).
    """
    provider_meta_block = f'''
  provider_meta "mongodbatlas" {{
    module_name    = "{module_name}"
    module_version = "{version}"
  }}
'''
    # Normalize content and split into lines
    lines = content.rstrip("\n").split("\n")

    # Find the start of the terraform block
    terraform_start_index: int | None = None
    terraform_block_pattern = re.compile(r"^\s*terraform\s*\{")
    for idx, line in enumerate(lines):
        if terraform_block_pattern.search(line):
            terraform_start_index = idx
            break

    # If no terraform block is found, return None to signal failure
    if terraform_start_index is None:
        return None

    # Walk forward from the terraform block start to find its matching closing brace
    brace_depth = 0
    closing_index: int | None = None
    for idx in range(terraform_start_index, len(lines)):
        line = lines[idx]
        brace_depth += line.count("{")
        brace_depth -= line.count("}")
        if brace_depth == 0:
            closing_index = idx
            break

    # If we couldn't find a proper closing brace, return None to signal failure
    if closing_index is None:
        return None

    # Insert provider_meta block just before the closing brace of the terraform block
    lines.insert(closing_index, provider_meta_block.rstrip())
    return "\n".join(lines) + "\n"


def update_versions_tf(
    file_path: Path, version: str, relative_path: str, module_name: str | None
) -> None:
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    content = file_path.read_text(encoding="utf-8")

    # Skip files that don't use mongodbatlas provider
    if not has_mongodbatlas_provider(content):
        print(f"-- Skipped {relative_path}: no mongodbatlas provider")
        return

    if has_provider_meta(content):
        # Existing behavior: update module_version
        replacement = f'module_version = "{version}"'
        new_content = re.sub(MODULE_VERSION_PATTERN, replacement, content)
        if content == new_content:
            print(
                f"Warning: No module_version found or already set to {version} in {relative_path}",
                file=sys.stderr,
            )
        file_path.write_text(new_content, encoding="utf-8")
        print(f'ok Updated {relative_path}: module_version = "{version}"')
    else:
        # New behavior: inject provider_meta block
        if not module_name:
            print(
                f"Warning: Cannot add provider_meta to {relative_path}: "
                "module_name not found in root versions.tf",
                file=sys.stderr,
            )
            return
        new_content = inject_provider_meta(content, module_name, version)
        if new_content is None:
            print(
                f"Warning: Could not find terraform block to inject provider_meta "
                f"in {relative_path}; leaving file unchanged.",
                file=sys.stderr,
            )
            return
        file_path.write_text(new_content, encoding="utf-8")
        print(
            f"ok Added provider_meta to {relative_path}: "
            f'module_name = "{module_name}", module_version = "{version}"'
        )


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: update_version.py <version>", file=sys.stderr)
        sys.exit(1)
    version_with_v = sys.argv[1]
    version = extract_version_number(version_with_v)
    repo_root = Path(__file__).parent.parent.parent
    module_name = get_module_name_from_root(repo_root)
    if not module_name:
        print(
            "Warning: Could not extract module_name from root versions.tf",
            file=sys.stderr,
        )
    for version_file in repo_root.rglob("versions.tf"):
        update_versions_tf(
            version_file, version, str(version_file.relative_to(repo_root)), module_name
        )


if __name__ == "__main__":
    main()
