"""Orchestrate workspace test workflows: gen -> plan -> reg."""

from __future__ import annotations

import enum
from pathlib import Path

import typer

from workspace import gen, models, output_assertions, plan, reg

app = typer.Typer()


class RunMode(enum.StrEnum):
    SETUP_ONLY = "setup-only"
    PLAN_ONLY = "plan-only"
    PLAN_SNAPSHOT_TEST = "plan-snapshot-test"
    APPLY = "apply"
    DESTROY = "destroy"
    CHECK_OUTPUTS = "check-outputs"


@app.command()
def main(
    mode: RunMode = typer.Option(RunMode.PLAN_ONLY, "--mode", "-m"),
    include_examples: str = typer.Option("all", "--include-examples", "-e"),
    auto_approve: bool = typer.Option(False, "--auto-approve"),
    skip_init: bool = typer.Option(False, "--skip-init"),
    ws: str = typer.Option("all", "--ws"),
    tests_dir: Path = typer.Option(models.DEFAULT_TESTS_DIR, "--tests-dir"),
    var_file: list[Path] = typer.Option([], "--var-file", "-v"),
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

    examples = "none" if mode == RunMode.SETUP_ONLY else include_examples

    for ws_dir in ws_dirs:
        typer.echo(f"=== {ws_dir.name} ({mode}) ===")
        gen.process_workspace(ws_dir, include_examples=examples)

        if not skip_init:
            plan.run_terraform_init(ws_dir)

        if mode in (RunMode.PLAN_ONLY, RunMode.PLAN_SNAPSHOT_TEST):
            plan.run_terraform_plan(ws_dir, var_file, skip_init=True)

        if mode == RunMode.PLAN_SNAPSHOT_TEST:
            reg.process_workspace(
                ws_dir,
                force_regen=force_regen,
                show_uncovered=show_uncovered,
            )

        if mode in (RunMode.SETUP_ONLY, RunMode.APPLY):
            plan.run_terraform_apply(ws_dir, var_file, auto_approve)

        if mode == RunMode.CHECK_OUTPUTS:
            output_assertions.process_workspace(ws_dir, include_examples)

        if mode == RunMode.DESTROY:
            plan.run_terraform_destroy(ws_dir, var_file, auto_approve)

    typer.echo("Done.")


if __name__ == "__main__":
    app()
