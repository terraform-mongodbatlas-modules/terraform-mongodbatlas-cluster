#!/usr/bin/env python
"""Run terraform plan for workspace tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

import typer
from tf_ws.models import DEFAULT_TESTS_DIR, resolve_workspaces

app = typer.Typer()

PLAN_BIN = "plan.bin"
PLAN_JSON = "plan.json"
INIT_MAX_RETRIES = 3


def run_cmd(cmd: list[str], cwd: Path) -> int:
    result = subprocess.run(cmd, cwd=cwd)
    return result.returncode


def run_terraform_init(ws_dir: Path, retries: int = INIT_MAX_RETRIES) -> None:
    for attempt in range(1, retries + 1):
        typer.echo(
            f"Running terraform init in {ws_dir.name} (attempt {attempt}/{retries})..."
        )
        if run_cmd(["terraform", "init", "-upgrade", "-input=false"], ws_dir) == 0:
            return
        if attempt < retries:
            typer.echo("Init failed, retrying...")
    typer.echo("terraform init failed after all retries", err=True)
    raise typer.Exit(1)


def run_terraform_plan(
    ws_dir: Path, var_files: list[Path], skip_init: bool = False
) -> None:
    if not skip_init:
        run_terraform_init(ws_dir)
    plan_cmd = ["terraform", "plan", f"-out={PLAN_BIN}", "-input=false"]
    for vf in var_files:
        plan_cmd.extend(["-var-file", str(vf)])
    typer.echo("Running terraform plan...")
    if run_cmd(plan_cmd, ws_dir) != 0:
        raise typer.Exit(1)
    typer.echo("Exporting plan to JSON...")
    plan_json_path = ws_dir / PLAN_JSON
    with open(plan_json_path, "w") as f:
        subprocess.run(
            ["terraform", "show", "-json", PLAN_BIN], cwd=ws_dir, stdout=f, check=True
        )
    typer.echo(f"Plan saved to {PLAN_JSON}")


def run_terraform_apply(
    ws_dir: Path, var_files: list[Path], auto_approve: bool = False
) -> None:
    apply_cmd = ["terraform", "apply", "-input=false"]
    for vf in var_files:
        apply_cmd.extend(["-var-file", str(vf)])
    if auto_approve:
        apply_cmd.append("-auto-approve")
    typer.echo("Running terraform apply...")
    if run_cmd(apply_cmd, ws_dir) != 0:
        raise typer.Exit(1)


def run_terraform_destroy(
    ws_dir: Path, var_files: list[Path], auto_approve: bool = False
) -> None:
    destroy_cmd = ["terraform", "destroy", "-input=false"]
    for vf in var_files:
        destroy_cmd.extend(["-var-file", str(vf)])
    if auto_approve:
        destroy_cmd.append("-auto-approve")
    typer.echo("Running terraform destroy...")
    if run_cmd(destroy_cmd, ws_dir) != 0:
        raise typer.Exit(1)


@app.command()
def main(
    ws: str = typer.Option(
        "all", "--ws", help="Workspace name or 'all' for all ws_* directories"
    ),
    tests_dir: Path = typer.Option(
        DEFAULT_TESTS_DIR, "--tests-dir", help="Path to tests directory"
    ),
    var_file: list[Path] = typer.Option(
        [], "--var-file", "-v", help="Variable files to pass to terraform plan"
    ),
) -> None:
    """Run terraform plan for a workspace."""
    try:
        ws_dirs = resolve_workspaces(ws, tests_dir)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    for ws_dir in ws_dirs:
        run_terraform_plan(ws_dir, var_file)
    typer.echo("Done.")


if __name__ == "__main__":
    app()
