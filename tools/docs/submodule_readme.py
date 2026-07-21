"""Transform submodule README.md code blocks to use registry source."""

import argparse
import re
from pathlib import Path

from release import tf_registry_source


def transform_submodule_source(
    content: str, registry_source: str, submodule_name: str, version: str | None = None
) -> str:
    local_pattern = rf'source\s*=\s*"[^"]*modules/{re.escape(submodule_name)}"'
    registry_submodule = f"{registry_source}//modules/{submodule_name}"
    transformed = re.sub(local_pattern, f'source  = "{registry_submodule}"', content)
    if version:
        version_without_v = version.removeprefix("v")
        transformed = re.sub(
            rf'(source\s*=\s*"{re.escape(registry_submodule)}")',
            rf'\1\n  version = "{version_without_v}"',
            transformed,
        )
    return transformed


def process_submodule_readme(
    submodule_dir: Path, registry_source: str, version: str | None = None
) -> bool:
    readme_path = submodule_dir / "README.md"
    if not readme_path.exists():
        return False
    submodule_name = submodule_dir.name
    content = readme_path.read_text(encoding="utf-8")
    transformed = transform_submodule_source(content, registry_source, submodule_name, version)
    if transformed != content:
        readme_path.write_text(transformed, encoding="utf-8")
        print(f"Updated {readme_path}")
        return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Transform submodule README source paths")
    parser.add_argument("--version", help="Version to add (e.g., v0.2.0)")
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent.parent
    modules_dir = repo_root / "modules"

    if not modules_dir.exists():
        print("No modules directory found")
        return

    registry_source = tf_registry_source.get_registry_source()
    updated = 0

    for submodule_dir in sorted(modules_dir.iterdir()):
        if submodule_dir.is_dir():
            if process_submodule_readme(submodule_dir, registry_source, args.version):
                updated += 1

    print(f"Processed {updated} submodule README(s)")


if __name__ == "__main__":
    main()
