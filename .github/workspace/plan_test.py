from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

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
      version = "~> 2.1"
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
      version = "~> 2.1"
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
      version = "~> 2.1"
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
    result = subprocess.CompletedProcess(
        args=["terraform", "init"],
        returncode=0,
        stdout="Installing mongodb/mongodbatlas v2.1.0\n",
        stderr="Terraform initialized with warnings\n",
    )
    monkeypatch.setattr(tf_retry, "run_terraform_init", lambda *_: result)

    run_terraform_init(tmp_path)

    captured = capsys.readouterr()
    assert captured.out == "Installing mongodb/mongodbatlas v2.1.0\n"
    assert captured.err == "Terraform initialized with warnings\n"


def test_strip_and_restore(tmp_path: Path):
    ex_dir = tmp_path / "01_basic"
    ex_dir.mkdir()
    vf = ex_dir / "versions.tf"
    vf.write_text(VERSIONS_TF_WITH_PROVIDER)

    with strip_provider_blocks([ex_dir]):
        content = vf.read_text()
        assert 'provider "mongodbatlas"' not in content
        assert 'provider_meta "mongodbatlas"' in content
        assert "terraform {" in content

    assert vf.read_text() == VERSIONS_TF_WITH_PROVIDER


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


def test_strip_multiline_provider(tmp_path: Path):
    ex_dir = tmp_path / "01_basic"
    ex_dir.mkdir()
    vf = ex_dir / "versions.tf"
    vf.write_text(VERSIONS_TF_WITH_MULTILINE_PROVIDER)

    with strip_provider_blocks([ex_dir]):
        content = vf.read_text()
        assert 'provider "mongodbatlas"' not in content
        assert "default_tags" not in content
        assert 'provider_meta "mongodbatlas"' in content
        assert "terraform {" in content

    assert vf.read_text() == VERSIONS_TF_WITH_MULTILINE_PROVIDER


def test_missing_versions_tf(tmp_path: Path):
    ex_dir = tmp_path / "01_basic"
    ex_dir.mkdir()

    with strip_provider_blocks([ex_dir]):
        assert not (ex_dir / "versions.tf").exists()


def test_provider_version_override_is_temporary(tmp_path: Path):
    override_path = tmp_path / PROVIDER_VERSION_OVERRIDE_FILE
    assert override_path.name.endswith("_override.tf")

    with provider_version_override(tmp_path, "2.1.0"):
        assert (
            override_path.read_text()
            == """\
terraform {
  required_providers {
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "= 2.1.0"
    }
  }
}
"""
        )

    assert not override_path.exists()


def test_provider_version_override_is_removed_on_exception(tmp_path: Path):
    override_path = tmp_path / PROVIDER_VERSION_OVERRIDE_FILE

    with pytest.raises(RuntimeError, match="boom"):
        with provider_version_override(tmp_path, "2.1.0"):
            raise RuntimeError("boom")

    assert not override_path.exists()


def test_provider_version_override_refuses_existing_file(tmp_path: Path):
    override_path = tmp_path / PROVIDER_VERSION_OVERRIDE_FILE
    override_path.write_text("user content")

    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        with provider_version_override(tmp_path, "2.1.0"):
            pass

    assert override_path.read_text() == "user content"


def test_provider_version_override_rejects_non_exact_version(tmp_path: Path):
    with pytest.raises(ValueError, match="Invalid exact provider version"):
        with provider_version_override(tmp_path, "~> 2.1"):
            pass


def test_provider_version_override_without_version_preserves_existing_file(tmp_path: Path):
    override_path = tmp_path / PROVIDER_VERSION_OVERRIDE_FILE
    override_path.write_text("user content")

    with provider_version_override(tmp_path, None):
        assert override_path.read_text() == "user content"

    assert override_path.read_text() == "user content"
