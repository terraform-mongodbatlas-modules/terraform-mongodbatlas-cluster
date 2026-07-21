from pathlib import Path

import pytest
from typer.testing import CliRunner

from dev import VERSIONS_FILE
from dev.test_compat import load_versions
from workspace import version_config
from workspace.version_config import Lane, app, select_terraform_version

RUNNER = CliRunner()


@pytest.mark.parametrize(
    ("lane", "expected"),
    [
        (Lane.MINIMUM, "1.9"),
        (Lane.MAXIMUM, "1.15"),
        (Lane.PROVIDER_HEAD, "1.15"),
    ],
)
def test_select_terraform_version(lane: Lane, expected: str):
    assert select_terraform_version(lane, ["1.9", "1.10", "1.15"]) == expected


def test_select_terraform_version_rejects_empty_list():
    with pytest.raises(ValueError, match="must not be empty"):
        select_terraform_version(Lane.MINIMUM, [])


def test_cli_writes_github_output(tmp_path: Path):
    output_path = tmp_path / "github-output"
    versions = load_versions(VERSIONS_FILE)
    expected = max(versions, key=lambda version: tuple(int(part) for part in version.split(".")))

    result = RUNNER.invoke(
        app,
        ["--lane", "provider-head", "--github-output", str(output_path)],
    )

    assert result.exit_code == 0
    assert output_path.read_text() == f"terraform_version={expected}\n"


def test_cli_reports_unquoted_numeric_version(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    config_path = tmp_path / ".terraform-versions.yaml"
    output_path = tmp_path / "github-output"
    config_path.write_text("versions: [1.10]\n")
    monkeypatch.setattr(version_config, "VERSIONS_FILE", config_path)

    result = RUNNER.invoke(
        app,
        ["--lane", "minimum", "--github-output", str(output_path)],
    )

    assert result.exit_code == 1
    assert result.output.startswith("Error: ")
    assert "versions must be strings" in result.output
    assert not output_path.exists()


def test_cli_reports_non_list_versions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    config_path = tmp_path / ".terraform-versions.yaml"
    output_path = tmp_path / "github-output"
    config_path.write_text('versions: "1.10"\n')
    monkeypatch.setattr(version_config, "VERSIONS_FILE", config_path)

    result = RUNNER.invoke(
        app,
        ["--lane", "minimum", "--github-output", str(output_path)],
    )

    assert result.exit_code == 1
    assert result.output.startswith("Error: ")
    assert "versions must be a list" in result.output
    assert not output_path.exists()
