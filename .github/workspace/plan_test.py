from __future__ import annotations

from pathlib import Path

import pytest

from workspace.plan import strip_provider_blocks

VERSIONS_TF_WITH_PROVIDER = """\
terraform {
  required_providers {
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "~> 2.0"
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
      version = "~> 2.0"
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
      version = "~> 2.0"
    }
  }
  required_version = ">= 1.9"

  provider_meta "mongodbatlas" {
    module_name    = "cluster"
    module_version = "local"
  }
}
"""


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
