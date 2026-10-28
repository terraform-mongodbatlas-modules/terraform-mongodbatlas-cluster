from __future__ import annotations

import logging
import subprocess
from pathlib import Path

import pytest
import typer

from shared import tf_retry
from workspace.plan import (
    PROVIDER_VERSION_OVERRIDE_FILE,
    provider_version_override,
    run_terraform_init,
    strip_provider_blocks,
)

VERSIONS_TF_WITH_PROVIDER = """\
terraform {
  required_providers {
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "~> 2.12"
    }
  }
  required_version = ">= 1.9"

  provider_meta "mongodbatlas" {
    module_name    = "cluster"
    module_version = "local"
  }
}

provider "mongodbatlas" {}
"""

VERSIONS_TF_WITH_MULTILINE_PROVIDER = """\
terraform {
  required_providers {
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "~> 2.12"
    }
  }
  required_version = ">= 1.9"

  provider_meta "mongodbatlas" {
    module_name    = "cluster"
    module_version = "local"
  }
}

provider "mongodbatlas" {
  default_tags {
    tags = {
      environment = "dev"
    }
  }
}
"""

VERSIONS_TF_WITHOUT_PROVIDER = """\
terraform {
  required_providers {
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "~> 2.12"
    }
  }
  required_version = ">= 1.9"

  provider_meta "mongodbatlas" {
    module_name    = "cluster"
    module_version = "local"
  }
}
"""


def test_run_terraform_init_prints_success_output(tmp_path: Path, monkeypatch, capsys):
    stdout = "Installing mongodb/mongodbatlas v2.12.0\n"
    stderr = "Terraform initialized with warnings\n"
    result = subprocess.CompletedProcess(
        args=["terraform", "init"],
        returncode=0,
        stdout=stdout,
        stderr=stderr,
    )
    monkeypatch.setattr(tf_retry, "run_terraform_init", lambda *_: result)

    run_terraform_init(tmp_path)

    captured = capsys.readouterr()
    assert (captured.out, captured.err) == (stdout, stderr)


def test_run_terraform_init_failure_logs_annotates_and_exits(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
):
    stderr = "Error: 100% failed\r\nno available releases match the given constraints " + "y" * 200

    def _raise(*_: object, **__: object) -> None:
        raise tf_retry.TerraformInitError(stderr, tmp_path)

    monkeypatch.setattr(tf_retry, "run_terraform_init", _raise)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")

    with (
        caplog.at_level(logging.ERROR, logger="workspace.plan"),
        pytest.raises(typer.Exit) as exc_info,
    ):
        run_terraform_init(tmp_path)

    assert exc_info.value.exit_code == 1
    assert stderr in caplog.text
    annotation = capsys.readouterr().out.rstrip("\n")
    assert annotation.startswith(f"::error::terraform init failed in {tmp_path}: ")
    assert "%25" in annotation
    assert "%0D" in annotation
    assert "%0A" in annotation
    assert "\n" not in annotation
    assert "\r" not in annotation


def test_run_terraform_init_failure_no_annotation_outside_github_actions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)

    def _raise(*_: object, **__: object) -> None:
        raise tf_retry.TerraformInitError("boom", tmp_path)

    monkeypatch.setattr(tf_retry, "run_terraform_init", _raise)

    with pytest.raises(typer.Exit):
        run_terraform_init(tmp_path)

    assert capsys.readouterr().out == ""


@pytest.mark.parametrize(
    "original",
    [VERSIONS_TF_WITH_PROVIDER, VERSIONS_TF_WITH_MULTILINE_PROVIDER],
    ids=["single-line", "multi-line"],
)
def test_strip_and_restore(tmp_path: Path, original: str):
    ex_dir = tmp_path / "01_basic"
    ex_dir.mkdir()
    vf = ex_dir / "versions.tf"
    vf.write_text(original)

    with strip_provider_blocks([ex_dir]):
        content = vf.read_text()
        assert 'provider "mongodbatlas"' not in content
        assert "default_tags" not in content
        assert 'provider_meta "mongodbatlas"' in content
        assert "terraform {" in content

    assert vf.read_text() == original


def test_restore_on_exception(tmp_path: Path):
    ex_dir = tmp_path / "01_basic"
    ex_dir.mkdir()
    vf = ex_dir / "versions.tf"
    vf.write_text(VERSIONS_TF_WITH_PROVIDER)

    with pytest.raises(RuntimeError, match="boom"):
        with strip_provider_blocks([ex_dir]):
            raise RuntimeError("boom")

    assert vf.read_text() == VERSIONS_TF_WITH_PROVIDER


def test_no_provider_block_unchanged(tmp_path: Path):
    ex_dir = tmp_path / "01_basic"
    ex_dir.mkdir()
    vf = ex_dir / "versions.tf"
    vf.write_text(VERSIONS_TF_WITHOUT_PROVIDER)

    with strip_provider_blocks([ex_dir]):
        assert vf.read_text() == VERSIONS_TF_WITHOUT_PROVIDER


def test_missing_versions_tf(tmp_path: Path):
    ex_dir = tmp_path / "01_basic"
    ex_dir.mkdir()

    with strip_provider_blocks([ex_dir]):
        assert not (ex_dir / "versions.tf").exists()


def test_provider_version_override_is_temporary(tmp_path: Path):
    override_path = tmp_path / PROVIDER_VERSION_OVERRIDE_FILE
    assert override_path.name.endswith("_override.tf")

    with provider_version_override(tmp_path, "2.12.0"):
        content = override_path.read_text()
        assert '"mongodb/mongodbatlas"' in content
        assert '"= 2.12.0"' in content

    assert not override_path.exists()


def test_provider_version_override_is_removed_on_exception(tmp_path: Path):
    override_path = tmp_path / PROVIDER_VERSION_OVERRIDE_FILE

    with pytest.raises(RuntimeError, match="boom"):
        with provider_version_override(tmp_path, "2.12.0"):
            raise RuntimeError("boom")

    assert not override_path.exists()


def test_provider_version_override_refuses_existing_file(tmp_path: Path):
    override_path = tmp_path / PROVIDER_VERSION_OVERRIDE_FILE
    override_path.write_text("user content")

    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        with provider_version_override(tmp_path, "2.12.0"):
            pass

    assert override_path.read_text() == "user content"


def test_provider_version_override_rejects_non_exact_version(tmp_path: Path):
    with pytest.raises(ValueError, match="Invalid exact provider version"):
        with provider_version_override(tmp_path, "~> 2.12"):
            pass
