from __future__ import annotations

import subprocess
from pathlib import Path

import typer
from tf_gen.config import FileType, GenerationTarget, load_config
from tf_gen.generators import (
    generate_main_tf,
    generate_outputs_tf,
    generate_variables_tf,
)
from tf_gen.schema.models import ResourceSchema
from tf_gen.schema.parser import extract_resource_schema, fetch_provider_schema
from tf_gen.section import make_markers, update_section

app = typer.Typer(no_args_is_help=True)


def _generate_file_content(
    schema: ResourceSchema,
    config: GenerationTarget,
    provider_name: str,
    file_type: FileType,
) -> str | None:
    match file_type:
        case FileType.variable:
            return generate_variables_tf(schema, config, provider_name)
        case FileType.resource:
            return generate_main_tf(schema, config, provider_name)
        case FileType.output:
            return generate_outputs_tf(schema, config, provider_name)


def _get_filename(config: GenerationTarget, file_type: FileType) -> str:
    match file_type:
        case FileType.variable:
            return config.variable_filename
        case FileType.resource:
            return config.resource_filename
        case FileType.output:
            return config.output_filename


def generate_for_target(
    schema: ResourceSchema,
    target: GenerationTarget,
    provider_name: str,
    config_filename: str,
    dest_path: Path,
) -> dict[str, str]:
    """Generate files for a single target. Returns {filepath: content}."""
    results: dict[str, str] = {}
    begin, end = make_markers(config_filename, target.resource_type)
    output_dir = dest_path / target.output_dir

    for file_type in target.files:
        content = _generate_file_content(schema, target, provider_name, file_type)
        if content is None:
            continue

        filename = _get_filename(target, file_type)
        filepath = output_dir / filename
        key = str(filepath)

        # Handle existing content or merge with previous results
        if key in results:
            existing = results[key]
        elif filepath.exists():
            existing = filepath.read_text()
        else:
            existing = ""

        results[key] = update_section(existing, begin, end, content)

    return results


def generate_for_config(
    config_path: Path,
    target: str | None = None,
    dest_path: Path | None = None,
    dry_run: bool = False,
    provider_defaults: dict[str, dict[str, str]] | None = None,
    cache_dir: Path | None = None,
) -> dict[str, str]:
    """Core generation logic. Returns {filepath: content}."""
    if dest_path is None:
        dest_path = Path.cwd()

    configs = load_config(config_path, provider_defaults)
    config_filename = config_path.name
    all_results: dict[str, str] = {}
    schema_cache: dict[str, dict] = {}

    for provider_config in configs:
        cache_key = (
            f"{provider_config.provider_source}_{provider_config.provider_version}"
        )
        if cache_key not in schema_cache:
            schema_cache[cache_key] = fetch_provider_schema(
                provider_config.provider_source,
                provider_config.provider_version,
                cache_dir,
            )
        full_schema = schema_cache[cache_key]

        for resource_type, targets in provider_config.resources.items():
            if target and resource_type != target:
                continue
            resource_schema = extract_resource_schema(
                full_schema, provider_config.provider_name, resource_type
            )
            for gen_target in targets:
                results = generate_for_target(
                    resource_schema,
                    gen_target,
                    provider_config.provider_name,
                    config_filename,
                    dest_path,
                )
                all_results.update(results)

    if not dry_run:
        _write_and_format(all_results)

    return all_results


def _write_and_format(results: dict[str, str]) -> None:
    """Write files and run terraform fmt."""
    for filepath, content in results.items():
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    # Run terraform fmt on all written files
    files = list(results.keys())
    if files:
        try:
            subprocess.run(
                ["terraform", "fmt"] + files, check=True, capture_output=True
            )
        except FileNotFoundError as e:
            msg = (
                "terraform CLI not found. Install terraform to format generated files."
            )
            raise RuntimeError(msg) from e
        except subprocess.CalledProcessError as e:
            msg = f"terraform fmt failed: {e.stderr.decode() if e.stderr else str(e)}"
            raise RuntimeError(msg) from e


@app.command()
def main(
    config: Path = typer.Option(..., "--config", "-c", help="Path to gen.yaml"),
    target: list[str] | None = typer.Option(
        None, "--target", "-t", help="Filter by resource type"
    ),
    dest_path: Path = typer.Option(
        Path.cwd(), "--dest-path", "-d", help="Base directory for output"
    ),
    cache_dir: Path | None = typer.Option(
        None,
        "--cache-dir",
        help="Directory to cache provider schemas (e.g., .tf-gen-cache)",
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print without writing"),
) -> None:
    """Generate Terraform files from provider schemas."""
    targets = target if target else [None]  # type: ignore[list-item]
    for t in targets:
        results = generate_for_config(
            config, target=t, dest_path=dest_path, dry_run=dry_run, cache_dir=cache_dir
        )
        if dry_run:
            for filepath, content in sorted(results.items()):
                typer.echo(f"=== {filepath} ===")
                typer.echo(content)
                typer.echo()


if __name__ == "__main__":
    app()
