#!/usr/bin/env python
"""Generate regression test files from terraform plan output."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

import typer
import yaml
from models import DumpConfig, WsConfig, parse_ws_config, sanitize_address

app = typer.Typer()

PLAN_JSON = "plan.json"
TEST_PLAN_REG_ACTUAL_DIR = "test_plan_reg_actual"


def parse_plan_json(plan_path: Path) -> dict[str, Any]:
    return json.loads(plan_path.read_text())


def extract_planned_resources(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Extract resources from planned_values, keyed by full address."""
    result: dict[str, dict[str, Any]] = {}
    _extract_from_module(
        plan.get("planned_values", {}).get("root_module", {}), "", result
    )
    return result


def _extract_from_module(
    module: dict[str, Any], prefix: str, result: dict[str, dict[str, Any]]
) -> None:
    for resource in module.get("resources", []):
        addr = f"{prefix}{resource['address']}" if prefix else resource["address"]
        result[addr] = resource.get("values", {})
    for child in module.get("child_modules", []):
        child_addr = child.get("address", "")
        new_prefix = f"{child_addr}." if child_addr else prefix
        _extract_from_module(child, new_prefix, result)


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
            addr = reg.address
            if addr not in resources:
                typer.echo(f"  Warning: {addr} not found in plan", err=True)
                continue
            filename = f"{ex.number:02d}_{sanitize_address(addr)}.yaml"
            content = dump_resource_yaml(resources[addr], config, reg.dump)
            (actual_dir / filename).write_text(content)
            typer.echo(f"  Generated {filename}")
    typer.echo(f"Running pytest for {ws_dir.name}...")
    pytest_args = ["pytest", str(ws_dir / "test_plan_reg.py"), "-v"]
    if force_regen:
        pytest_args.append("--force-regen")
    result = subprocess.run(pytest_args, cwd=ws_dir)
    if result.returncode != 0:
        raise typer.Exit(result.returncode)


@app.command()
def main(
    ws_path: Path = typer.Argument(
        ..., help="Path to workspace directory or tests/{ws_name}"
    ),
    force_regen: bool = typer.Option(
        False, "--force-regen", help="Force regenerate baseline files"
    ),
) -> None:
    """Generate regression test files and run pytest."""
    if ws_path.name == "all":
        tests_dir = ws_path.parent
        ws_dirs = sorted(
            d for d in tests_dir.iterdir() if d.is_dir() and d.name.startswith("ws_")
        )
        for ws_dir in ws_dirs:
            process_workspace(ws_dir, force_regen)
    else:
        if not ws_path.exists():
            typer.echo(f"Error: {ws_path} does not exist", err=True)
            raise typer.Exit(1)
        process_workspace(ws_path, force_regen)
    typer.echo("Done.")


if __name__ == "__main__":
    app()
