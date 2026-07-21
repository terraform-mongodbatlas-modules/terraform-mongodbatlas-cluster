"""Select the Terraform version for a plan snapshot lane."""

from __future__ import annotations

import enum
from pathlib import Path

import typer
import yaml

from dev import VERSIONS_FILE
from dev.test_compat import load_versions

app = typer.Typer()


class Lane(enum.StrEnum):
    MINIMUM = "minimum"
    MAXIMUM = "maximum"
    PROVIDER_HEAD = "provider-head"


def version_key(version: str) -> tuple[int, ...]:
    """Return a numerically comparable version key."""
    return tuple(int(part) for part in version.split("."))


def select_terraform_version(lane: Lane, versions: list[str]) -> str:
    """Select the minimum Terraform version or the maximum for every other lane."""
    if not isinstance(versions, list):
        raise TypeError(f"{VERSIONS_FILE}: versions must be a list")
    if not versions:
        raise ValueError(f"{VERSIONS_FILE}: versions must not be empty")
    if any(not isinstance(version, str) for version in versions):
        raise TypeError(f"{VERSIONS_FILE}: versions must be strings")
    selector = min if lane == Lane.MINIMUM else max
    return selector(versions, key=version_key)


@app.command()
def main(
    lane: Lane = typer.Option(..., "--lane"),
    github_output: Path = typer.Option(..., "--github-output"),
) -> None:
    """Write the selected Terraform version to the GitHub Actions output file."""
    try:
        version = select_terraform_version(lane, load_versions(VERSIONS_FILE))
        with github_output.open("a", encoding="utf-8") as output:
            output.write(f"terraform_version={version}\n")
    except (KeyError, OSError, TypeError, ValueError, yaml.YAMLError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1) from exc

    typer.echo(version)


if __name__ == "__main__":
    app()
