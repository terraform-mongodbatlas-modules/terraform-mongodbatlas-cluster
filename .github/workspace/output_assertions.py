"""Run output assertions after terraform apply."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import typer

from workspace import gen, models, plan

app = typer.Typer()

EXAMPLE_OUTPUT_PREFIX = "ex_"


def _extract_example_outputs(
    raw_outputs: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for key, entry in raw_outputs.items():
        if not key.startswith(EXAMPLE_OUTPUT_PREFIX):
            continue
        example_id = key.removeprefix(EXAMPLE_OUTPUT_PREFIX)
        value = entry.get("value", {})
        result[example_id] = value if isinstance(value, dict) else {}
    return result


def _check_assertion(value: Any, assertion: models.OutputAssertion) -> str:
    if assertion.not_empty:
        if value is None or value == "" or value == {}:
            return f"expected non-empty value, got {value!r}"
    if assertion.pattern:
        str_value = str(value) if value is not None else ""
        if not re.search(assertion.pattern, str_value):
            return f"pattern {assertion.pattern!r} did not match {str_value!r}"
    return ""


def run_output_assertions(config: models.WsConfig, raw_outputs: dict[str, Any]) -> bool:
    example_outputs = _extract_example_outputs(raw_outputs)
    all_passed = True
    for ex in config.examples:
        if not ex.output_assertions:
            continue
        outputs = example_outputs.get(ex.identifier, {})
        for assertion in ex.output_assertions:
            value = outputs.get(assertion.output)
            if error := _check_assertion(value, assertion):
                typer.echo(
                    f"  FAIL: {ex.identifier}.{assertion.output}: {error}",
                    err=True,
                )
                all_passed = False
            else:
                typer.echo(f"  PASS: {ex.identifier}.{assertion.output}")
    return all_passed


def process_workspace(ws_dir: Path, include_examples: str = "all") -> None:
    ws_config_path = ws_dir / models.WORKSPACE_CONFIG_FILE
    if not ws_config_path.exists():
        typer.echo(f"Skipping {ws_dir.name}: no {models.WORKSPACE_CONFIG_FILE} found")
        return
    config = models.parse_ws_config(ws_config_path)
    examples = gen.parse_include_examples(include_examples, config)
    filtered_config = models.WsConfig(examples=examples, var_groups=config.var_groups)
    has_assertions = any(ex.output_assertions for ex in filtered_config.examples)
    if not has_assertions:
        typer.echo(f"  No output_assertions configured in {ws_dir.name}, skipping")
        return
    raw_outputs = plan.run_terraform_output_json(ws_dir)
    typer.echo("Running output assertions...")
    if not run_output_assertions(filtered_config, raw_outputs):
        typer.echo("Output assertions FAILED", err=True)
        raise typer.Exit(1)
    typer.echo("All output assertions passed")


@app.command()
def main(
    ws: str = typer.Option("all", "--ws"),
    tests_dir: Path = typer.Option(models.DEFAULT_TESTS_DIR, "--tests-dir"),
    include_examples: str = typer.Option("all", "--include-examples", "-e"),
) -> None:
    try:
        ws_dirs = models.resolve_workspaces(ws, tests_dir)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    for ws_dir in ws_dirs:
        process_workspace(ws_dir, include_examples)
    typer.echo("Done.")


if __name__ == "__main__":
    app()
