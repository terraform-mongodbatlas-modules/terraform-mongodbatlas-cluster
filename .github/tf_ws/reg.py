#!/usr/bin/env python
"""Generate regression test files from terraform plan output."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import typer
import yaml
from tf_ws.models import (
    DEFAULT_TESTS_DIR,
    DumpConfig,
    WsConfig,
    parse_ws_config,
    sanitize_address,
)

app = typer.Typer()

PLAN_JSON = "plan.json"
TEST_PLAN_REG_ACTUAL_DIR = "test_plan_reg_actual"


def parse_plan_json(plan_path: Path) -> dict[str, Any]:
    return json.loads(plan_path.read_text())


def extract_planned_resources(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Extract resources from planned_values, keyed by full address."""
    result: dict[str, dict[str, Any]] = {}
    _extract_from_module(plan.get("planned_values", {}).get("root_module", {}), result)
    return result


def _extract_from_module(
    module: dict[str, Any], result: dict[str, dict[str, Any]]
) -> None:
    for resource in module.get("resources", []):
        result[resource["address"]] = resource.get("values", {})
    for child in module.get("child_modules", []):
        _extract_from_module(child, result)


def filter_values(
    values: dict[str, Any], skip_attrs: list[str], skip_values: list[str]
) -> dict[str, Any]:
    """Remove attributes matching skip criteria."""
    filtered: dict[str, Any] = {}
    for key, val in values.items():
        if key in skip_attrs:
            continue
        if val is None and "null" in skip_values:
            continue
        if isinstance(val, str) and any(sv in val for sv in skip_values):
            continue
        if isinstance(val, dict):
            val = filter_values(val, skip_attrs, skip_values)
        elif isinstance(val, list):
            val = [
                filter_values(v, skip_attrs, skip_values) if isinstance(v, dict) else v
                for v in val
            ]
        filtered[key] = val
    return filtered


def dump_resource_yaml(
    values: dict[str, Any], config: WsConfig, dump_config: DumpConfig
) -> str:
    skip_attrs = config.skip_attributes() + dump_config.skip_lines.substring_attributes
    skip_values = dump_config.skip_lines.substring_values
    if "null" not in skip_values:
        skip_values = skip_values + ["null"]
    filtered = filter_values(values, skip_attrs, skip_values)
    return yaml.dump(
        filtered, default_flow_style=False, sort_keys=True, allow_unicode=True
    )


def find_matching_address(
    resources: dict[str, dict[str, Any]], suffix: str, example_num: int
) -> str | None:
    """Find resource address ending with suffix, preferring example module prefix."""
    example_prefix = f"module.ex_{example_num:02d}."
    for addr in resources:
        if addr.endswith(suffix) and addr.startswith(example_prefix):
            return addr
    for addr in resources:
        if addr.endswith(suffix):
            return addr
    return None


def process_workspace(ws_dir: Path, force_regen: bool) -> None:
    ws_yaml = ws_dir / "ws.yaml"
    plan_path = ws_dir / PLAN_JSON
    if not ws_yaml.exists():
        typer.echo(f"Skipping {ws_dir.name}: no ws.yaml found")
        return
    if not plan_path.exists():
        typer.echo(
            f"Skipping {ws_dir.name}: no {PLAN_JSON} found (run test-ws-plan first)"
        )
        return
    config = parse_ws_config(ws_yaml)
    plan = parse_plan_json(plan_path)
    resources = extract_planned_resources(plan)
    actual_dir = ws_dir / TEST_PLAN_REG_ACTUAL_DIR
    actual_dir.mkdir(exist_ok=True)
    for ex in config.examples:
        for reg in ex.plan_regressions:
            full_addr = find_matching_address(resources, reg.address, ex.number)
            if not full_addr:
                typer.echo(f"  Warning: {reg.address} not found in plan", err=True)
                continue
            filename = f"{ex.number:02d}_{sanitize_address(reg.address)}.yaml"
            content = dump_resource_yaml(resources[full_addr], config, reg.dump)
            (actual_dir / filename).write_text(content)
            typer.echo(f"  Generated {filename}")
    typer.echo(f"Running pytest for {ws_dir.name}...")
    pytest_args = ["pytest", "test_plan_reg.py", "-v"]
    if force_regen:
        pytest_args.append("--force-regen")
    result = subprocess.run(pytest_args, cwd=ws_dir)
    if result.returncode != 0:
        raise typer.Exit(result.returncode)


@app.command()
def main(
    ws: str = typer.Option(
        "all", "--ws", help="Workspace name or 'all' for all ws_* directories"
    ),
    tests_dir: Path = typer.Option(
        DEFAULT_TESTS_DIR, "--tests-dir", help="Path to tests directory"
    ),
    force_regen: bool = typer.Option(
        False, "--force-regen", help="Force regenerate baseline files"
    ),
) -> None:
    """Generate regression test files and run pytest."""
    if ws == "all":
        ws_dirs = sorted(
            d for d in tests_dir.iterdir() if d.is_dir() and d.name.startswith("ws_")
        )
        for ws_dir in ws_dirs:
            process_workspace(ws_dir, force_regen)
    else:
        ws_path = tests_dir / ws
        if not ws_path.exists():
            typer.echo(f"Error: {ws_path} does not exist", err=True)
            raise typer.Exit(1)
        process_workspace(ws_path, force_regen)
    typer.echo("Done.")


if __name__ == "__main__":
    app()
