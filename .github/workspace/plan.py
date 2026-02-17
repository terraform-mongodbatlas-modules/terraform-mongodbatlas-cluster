"""Run terraform plan for workspace tests."""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import Any

import typer

from shared import tf_retry
from workspace import models

logger = logging.getLogger(__name__)

app = typer.Typer()

PLAN_BIN = "plan.bin"
PLAN_JSON = "plan.json"
OUTPUTS_ACTUAL_JSON = "outputs_actual.json"


def run_cmd(cmd: list[str], cwd: Path) -> int:
    result = subprocess.run(cmd, cwd=cwd)
    return result.returncode


def run_terraform_init(ws_dir: Path) -> None:
    logger.info(f"Running terraform init in {ws_dir.name}...")
    try:
        tf_retry.run_terraform_init(["terraform", "init", "-upgrade", "-input=false"], ws_dir)
    except tf_retry.TerraformInitError as e:
        logger.error(f"terraform init failed: {e.stderr[:200]}")
        raise typer.Exit(1) from e


def run_terraform_plan(ws_dir: Path, var_files: list[Path], skip_init: bool = False) -> None:
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
        subprocess.run(["terraform", "show", "-json", PLAN_BIN], cwd=ws_dir, stdout=f, check=True)
    typer.echo(f"Plan saved to {PLAN_JSON}")


def run_terraform_apply(ws_dir: Path, var_files: list[Path], auto_approve: bool = False) -> None:
    apply_cmd = ["terraform", "apply", "-input=false"]
    for vf in var_files:
        apply_cmd.extend(["-var-file", str(vf)])
    if auto_approve:
        apply_cmd.append("-auto-approve")
    typer.echo("Running terraform apply...")
    if run_cmd(apply_cmd, ws_dir) != 0:
        raise typer.Exit(1)


def run_terraform_output_json(ws_dir: Path) -> dict[str, Any]:
    typer.echo("Capturing terraform output...")
    result = subprocess.run(
        ["terraform", "output", "-json"],
        cwd=ws_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        typer.echo(f"terraform output failed: {result.stderr}", err=True)
        raise typer.Exit(1)
    outputs = json.loads(result.stdout)
    output_path = ws_dir / OUTPUTS_ACTUAL_JSON
    output_path.write_text(json.dumps(outputs, indent=2) + "\n")
    typer.echo(f"Outputs saved to {OUTPUTS_ACTUAL_JSON}")
    return outputs


def run_terraform_destroy(ws_dir: Path, var_files: list[Path], auto_approve: bool = False) -> None:
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
    ws: str = typer.Option("all", "--ws"),
    tests_dir: Path = typer.Option(models.DEFAULT_TESTS_DIR, "--tests-dir"),
    var_file: list[Path] = typer.Option([], "--var-file", "-v"),
) -> None:
    try:
        ws_dirs = models.resolve_workspaces(ws, tests_dir)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    for ws_dir in ws_dirs:
        run_terraform_plan(ws_dir, var_file)
    typer.echo("Done.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app()
