from __future__ import annotations

from pathlib import Path

from tf_utils.validate_versions_tf import (
    RootVersionsRef,
    _errors_for_file,
    parse_root_versions_reference,
)

_CLUSTER_ROOT = RootVersionsRef(
    providers={"mongodbatlas": ("~> 2.0", "mongodb/mongodbatlas")},
    required_version=">= 1.9",
)


def test_parse_root_versions_reference_matches_real_cluster_root() -> None:
    root = Path(__file__).resolve().parents[2]
    ref = parse_root_versions_reference(root)
    assert "mongodbatlas" in ref.providers
    assert ref.required_version == ">= 1.9"


def test_errors_for_file_valid(tmp_path: Path) -> None:
    vf = tmp_path / "versions.tf"
    vf.write_text(
        """\
terraform {
  required_providers {
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "~> 2.0"
    }
  }
  required_version = ">= 1.9"
}

provider "mongodbatlas" {}
""",
    )
    assert _errors_for_file(vf, vf.read_text(), _CLUSTER_ROOT) == []


def test_errors_for_file_rejects_version_mismatch(tmp_path: Path) -> None:
    vf = tmp_path / "versions.tf"
    vf.write_text(
        """\
terraform {
  required_providers {
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = ">= 2.0"
    }
  }
  required_version = ">= 1.9"
}
""",
    )
    errs = _errors_for_file(vf, vf.read_text(), _CLUSTER_ROOT)
    assert len(errs) == 1
    assert "mongodbatlas" in errs[0]
    assert "must match root" in errs[0]


def test_errors_for_file_rejects_required_version_mismatch(tmp_path: Path) -> None:
    vf = tmp_path / "versions.tf"
    vf.write_text(
        """\
terraform {
  required_providers {
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "~> 2.0"
    }
  }
  required_version = ">= 1.6"
}
""",
    )
    errs = _errors_for_file(vf, vf.read_text(), _CLUSTER_ROOT)
    assert len(errs) == 1
    assert "required_version" in errs[0]


def test_errors_for_file_missing_root_provider(tmp_path: Path) -> None:
    vf = tmp_path / "versions.tf"
    vf.write_text(
        """\
terraform {
  required_version = ">= 1.9"
  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "~> 2.0"
    }
  }
}
""",
    )
    errs = _errors_for_file(vf, vf.read_text(), _CLUSTER_ROOT)
    assert any("missing required_providers.mongodbatlas" in e for e in errs)


def test_errors_for_file_unparseable_hcl(tmp_path: Path) -> None:
    vf = tmp_path / "versions.tf"
    vf.write_text("terraform { this is not valid hcl2 }", encoding="utf-8")
    errs = _errors_for_file(vf, vf.read_text(), _CLUSTER_ROOT)
    assert len(errs) == 1
    assert "HCL parse error" in errs[0]


def test_errors_for_file_allows_extra_providers(tmp_path: Path) -> None:
    vf = tmp_path / "versions.tf"
    vf.write_text(
        """\
terraform {
  required_providers {
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "~> 2.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 2.0"
    }
  }
  required_version = ">= 1.9"
}
""",
    )
    assert _errors_for_file(vf, vf.read_text(), _CLUSTER_ROOT) == []
