#!/usr/bin/env python
"""Run terraform plan for workspace tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

import typer

app = typer.Typer()

PLAN_BIN = "plan.bin"
PLAN_JSON = "plan.json"


def run_cmd(cmd: list[str], cwd: Path) -> None:
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        raise typer.Exit(result.returncode)


def run_terraform_plan(ws_dir: Path, var_files: list[Path]) -> None:
    typer.echo(f"Running terraform init in {ws_dir.name}...")
    run_cmd(["terraform", "init", "-upgrade"], ws_dir)
    plan_cmd = ["terraform", "plan", f"-out={PLAN_BIN}"]
    for vf in var_files:
        plan_cmd.extend(["-var-file", str(vf)])
    typer.echo("Running terraform plan...")
    run_cmd(plan_cmd, ws_dir)
    typer.echo("Exporting plan to JSON...")
    plan_json_path = ws_dir / PLAN_JSON
    with open(plan_json_path, "w") as f:
        subprocess.run(
            ["terraform", "show", "-json", PLAN_BIN], cwd=ws_dir, stdout=f, check=True
        )
    typer.echo(f"Plan saved to {PLAN_JSON}")


def find_workspace(tests_dir: Path, ws_name: str) -> Path:
    if ws_name == "all":
        raise ValueError("Use 'all' only at top level")
    ws_dir = tests_dir / ws_name
    if not ws_dir.exists():
        for d in tests_dir.iterdir():
            if d.is_dir() and d.name.startswith("ws_") and ws_name in d.name:
                return d
        raise typer.Exit(1)
    return ws_dir


@app.command()
def main(
    ws_path: Path = typer.Argument(
        ..., help="Path to workspace directory or tests/{ws_name}"
    ),
    var_file: list[Path] = typer.Option(
        [], "--var-file", "-v", help="Variable files to pass to terraform plan"
    ),
) -> None:
    """Run terraform plan for a workspace."""
    if ws_path.name == "all":
        tests_dir = ws_path.parent
        ws_dirs = sorted(
            d for d in tests_dir.iterdir() if d.is_dir() and d.name.startswith("ws_")
        )
        for ws_dir in ws_dirs:
            run_terraform_plan(ws_dir, var_file)
    else:
        if not ws_path.exists():
            typer.echo(f"Error: {ws_path} does not exist", err=True)
            raise typer.Exit(1)
        run_terraform_plan(ws_path, var_file)
    typer.echo("Done.")


if __name__ == "__main__":
    app()
