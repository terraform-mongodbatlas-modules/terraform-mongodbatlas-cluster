"""Orchestrate workspace test workflows: gen -> plan -> reg."""

from __future__ import annotations

import enum
from pathlib import Path

import typer
from tf_ws import gen, plan, reg
from tf_ws.models import DEFAULT_TESTS_DIR, resolve_workspaces

app = typer.Typer()


class RunMode(enum.StrEnum):
    SETUP_ONLY = "setup-only"
    PLAN_ONLY = "plan-only"
    PLAN_REG = "plan-reg"
    APPLY = "apply"


@app.command()
def main(
    mode: RunMode = typer.Option(RunMode.PLAN_ONLY, "--mode", "-m"),
    include_examples: str = typer.Option("all", "--include-examples", "-e"),
    auto_approve: bool = typer.Option(False, "--auto-approve"),
    skip_init: bool = typer.Option(False, "--skip-init"),
    ws: str = typer.Option("all", "--ws"),
    tests_dir: Path = typer.Option(DEFAULT_TESTS_DIR, "--tests-dir"),
    var_file: list[Path] = typer.Option([], "--var-file", "-v"),
    force_regen: bool = typer.Option(False, "--force-regen"),
) -> None:
    """Orchestrate workspace test workflows."""
    try:
        ws_dirs = resolve_workspaces(ws, tests_dir)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    examples = "none" if mode == RunMode.SETUP_ONLY else include_examples

    for ws_dir in ws_dirs:
        typer.echo(f"=== {ws_dir.name} ({mode}) ===")
        gen.process_workspace(ws_dir, include_examples=examples)

        if not skip_init:
            plan.run_terraform_init(ws_dir)

        if mode in (RunMode.PLAN_ONLY, RunMode.PLAN_REG):
            plan.run_terraform_plan(ws_dir, var_file, skip_init=True)

        if mode == RunMode.PLAN_REG:
            reg.process_workspace(ws_dir, force_regen)

        if mode in (RunMode.SETUP_ONLY, RunMode.APPLY):
            plan.run_terraform_apply(ws_dir, auto_approve)

    typer.echo("Done.")


if __name__ == "__main__":
    app()
