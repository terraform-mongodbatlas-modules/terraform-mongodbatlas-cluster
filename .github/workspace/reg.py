"""Generate regression test files from terraform plan output."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import typer
import yaml

from workspace import models

app = typer.Typer()

PLAN_JSON = "plan.json"
PLAN_SNAPSHOTS_ACTUAL_DIR = "plan_snapshots_actual"
TEST_PLAN_SNAPSHOT_PY = "test_plan_snapshot.py"


def parse_plan_json(plan_path: Path) -> dict[str, Any]:
    return json.loads(plan_path.read_text())


def extract_planned_resources(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    _extract_from_module(plan.get("planned_values", {}).get("root_module", {}), result)
    return result


def _extract_from_module(module: dict[str, Any], result: dict[str, dict[str, Any]]) -> None:
    for resource in module.get("resources", []):
        result[resource["address"]] = resource.get("values", {})
    for child in module.get("child_modules", []):
        _extract_from_module(child, result)


def filter_values(
    values: dict[str, Any],
    skip_attrs: list[str],
    skip_values: list[str],
    redact_attrs: list[str],
) -> dict[str, Any]:
    filtered: dict[str, Any] = {}
    for key, val in values.items():
        if key in skip_attrs:
            continue
        if key in redact_attrs:
            filtered[key] = f"<{key}>"
            continue
        if val is None and "null" in skip_values:
            continue
        if isinstance(val, str) and any(sv in val for sv in skip_values):
            continue
        if isinstance(val, dict):
            val = filter_values(val, skip_attrs, skip_values, redact_attrs)
        elif isinstance(val, list):
            val = [
                filter_values(v, skip_attrs, skip_values, redact_attrs)
                if isinstance(v, dict)
                else v
                for v in val
            ]
        filtered[key] = val
    return filtered


def dump_resource_yaml(
    values: dict[str, Any], config: models.WsConfig, dump_config: models.DumpConfig
) -> str:
    skip_attrs = dump_config.skip_lines.substring_attributes
    skip_values = dump_config.skip_lines.substring_values
    if "null" not in skip_values:
        skip_values = skip_values + ["null"]
    redact_attrs = config.redact_var_attributes() + dump_config.skip_lines.redact_attributes
    if dump_config.skip_lines.use_default_redact:
        redact_attrs = redact_attrs + models.DEFAULT_REDACT_ATTRIBUTES
    filtered = filter_values(values, skip_attrs, skip_values, redact_attrs)
    return yaml.dump(filtered, default_flow_style=False, sort_keys=True, allow_unicode=True)


def find_matching_address(
    resources: dict[str, dict[str, Any]], address: str, example_id: str
) -> str | None:
    """Find a resource address in the plan that matches exactly.

    The address in plan_regressions must be the full path after the example prefix.
    For example, if the full plan address is:
        module.ex_encryption.module.atlas_azure.module.encryption[0].azurerm_role_assignment.key_vault_crypto

    The address in config should be:
        module.atlas_azure.module.encryption[0].azurerm_role_assignment.key_vault_crypto

    Args:
        resources: Dict of full resource addresses to their values from plan.json
        address: The exact address after the example prefix (from plan_regressions config)
        example_id: The example identifier (used to build module.ex_{id} prefix)

    Returns:
        The full matching address, or None if not found.
    """
    full_address = f"module.ex_{example_id}.{address}"
    if full_address in resources:
        return full_address
    return None


def find_uncovered_resources(
    resources: dict[str, dict[str, Any]],
    config: models.WsConfig,
) -> dict[str, list[str]]:
    """Find resources in plan that don't have plan_regressions entries."""
    uncovered: dict[str, list[str]] = {}
    for ex in config.examples:
        example_prefix = f"module.ex_{ex.identifier}."
        example_resources = {addr for addr in resources if addr.startswith(example_prefix)}
        covered = set()
        for reg in ex.plan_regressions:
            full_addr = find_matching_address(resources, reg.address, ex.identifier)
            if full_addr:
                covered.add(full_addr)
        missing = example_resources - covered
        if missing:
            uncovered[ex.identifier] = sorted(addr.removeprefix(example_prefix) for addr in missing)
    return uncovered


def categorize_address(addr: str) -> str:
    """Categorize an address for display hints."""
    if ".data." in addr or addr.startswith("data."):
        return "data"
    if not addr.startswith("module."):
        return "example"  # resource defined in example itself, not in module
    return "module"


def report_uncovered(uncovered: dict[str, list[str]]) -> None:
    """Print uncovered resources in a format ready to copy into config."""
    if not uncovered:
        typer.echo("  All resources are covered by plan_regressions")
        return
    typer.echo("")
    typer.echo("  Hints:")
    typer.echo("    - [data] = data sources (read-only, usually skip)")
    typer.echo("    - [example] = resources in example's main.tf (not in tested module)")
    typer.echo("    - [module] = resources inside the module being tested")
    typer.echo("")
    typer.echo("  Uncovered resources:")
    for example_id, addresses in uncovered.items():
        typer.echo(f"    # Example: {example_id} (module.ex_{example_id}.{{address}})")
        for addr in addresses:
            category = categorize_address(addr)
            typer.echo(f"      # [{category}] - address: {addr}")


def process_workspace(ws_dir: Path, force_regen: bool, show_uncovered: bool) -> None:
    ws_config = ws_dir / models.WORKSPACE_CONFIG_FILE
    plan_path = ws_dir / PLAN_JSON
    if not ws_config.exists():
        typer.echo(f"Skipping {ws_dir.name}: no {models.WORKSPACE_CONFIG_FILE} found")
        return
    if not plan_path.exists():
        typer.echo(f"Skipping {ws_dir.name}: no {PLAN_JSON} found (run plan first)")
        return
    config = models.parse_ws_config(ws_config)
    plan = parse_plan_json(plan_path)
    resources = extract_planned_resources(plan)
    if show_uncovered:
        uncovered = find_uncovered_resources(resources, config)
        report_uncovered(uncovered)
        return
    actual_dir = ws_dir / PLAN_SNAPSHOTS_ACTUAL_DIR
    actual_dir.mkdir(exist_ok=True)
    for ex in config.examples:
        nested = ex.should_use_nested_snapshots()
        if nested:
            example_dir = actual_dir / ex.identifier
            example_dir.mkdir(exist_ok=True)
        for reg in ex.plan_regressions:
            full_addr = find_matching_address(resources, reg.address, ex.identifier)
            if not full_addr:
                typer.echo(f"  Warning: {reg.address} not found in plan", err=True)
                continue
            sanitized = models.sanitize_address(reg.address)
            content = dump_resource_yaml(resources[full_addr], config, reg.dump)
            if nested:
                filepath = actual_dir / ex.identifier / f"{sanitized}.yaml"
                display_path = f"{ex.identifier}/{sanitized}.yaml"
            else:
                filepath = actual_dir / f"{ex.identifier}_{sanitized}.yaml"
                display_path = f"{ex.identifier}_{sanitized}.yaml"
            filepath.write_text(content)
            typer.echo(f"  Generated {display_path}")
    typer.echo(f"Running pytest for {ws_dir.name}...")
    pytest_args = ["pytest", TEST_PLAN_SNAPSHOT_PY, "-v"]
    if force_regen:
        pytest_args.append("--force-regen")
    result = subprocess.run(pytest_args, cwd=ws_dir)
    if result.returncode != 0:
        raise typer.Exit(result.returncode)


@app.command()
def main(
    ws: str = typer.Option("all", "--ws"),
    tests_dir: Path = typer.Option(models.DEFAULT_TESTS_DIR, "--tests-dir"),
    force_regen: bool = typer.Option(False, "--force-regen"),
    show_uncovered: bool = typer.Option(
        False,
        "--show-uncovered",
        "-u",
        help="Show resources not covered by plan_regressions",
    ),
) -> None:
    try:
        ws_dirs = models.resolve_workspaces(ws, tests_dir)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    for ws_dir in ws_dirs:
        process_workspace(ws_dir, force_regen, show_uncovered)
    typer.echo("Done.")


if __name__ == "__main__":
    app()
