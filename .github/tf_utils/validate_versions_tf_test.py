# path-sync copy -n sdlc
from __future__ import annotations

from pathlib import Path

from tf_utils.validate_versions_tf import (
    RootVersionsRef,
    _errors_for_file,
    _load_provider_version_exceptions,
    parse_root_versions_reference,
    validate_repo,
)

_CLUSTER_ROOT = RootVersionsRef(
    providers={"mongodbatlas": ("~> 2.0", "mongodb/mongodbatlas")},
    required_version=">= 1.9",
)

_AWS_REPO_STYLE_ROOT = RootVersionsRef(
    providers={
        "mongodbatlas": ("~> 2.11", "mongodb/mongodbatlas"),
        "aws": (">= 6.0", "hashicorp/aws"),
    },
    required_version=">= 1.9",
)


_REAL_REPO_ROOT = Path(__file__).resolve().parents[2]


def test_parse_root_versions_reference_matches_real_cluster_root() -> None:
    ref = parse_root_versions_reference(_REAL_REPO_ROOT)
    assert "mongodbatlas" in ref.providers
    assert ref.required_version == ">= 1.9"


def test_validate_repo_passes_on_real_repo() -> None:
    assert validate_repo(_REAL_REPO_ROOT) == []


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
    (tmp_path / "main.tf").write_text(
        'resource "mongodbatlas_project" "x" { org_id = "o" name = "n" }\n',
        encoding="utf-8",
    )
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


def test_errors_for_file_allows_omitting_unused_root_provider_aws(tmp_path: Path) -> None:
    (tmp_path / "main.tf").write_text(
        """\
resource "mongodbatlas_encryption_at_rest_private_endpoint" "this" {
  project_id     = "p"
  cloud_provider = "AWS"
  region_name    = "US_EAST_1"
}
""",
        encoding="utf-8",
    )
    vf = tmp_path / "versions.tf"
    vf.write_text(
        """\
terraform {
  required_version = ">= 1.9"
  required_providers {
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "~> 2.11"
    }
  }
}
""",
        encoding="utf-8",
    )
    assert _errors_for_file(vf, vf.read_text(), _AWS_REPO_STYLE_ROOT) == []


def test_errors_for_file_requires_root_provider_when_used(tmp_path: Path) -> None:
    (tmp_path / "main.tf").write_text(
        'resource "aws_instance" "x" { ami = "a" instance_type = "t3.micro" }\n',
        encoding="utf-8",
    )
    vf = tmp_path / "versions.tf"
    vf.write_text(
        """\
terraform {
  required_version = ">= 1.9"
  required_providers {
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "~> 2.11"
    }
  }
}
""",
        encoding="utf-8",
    )
    errs = _errors_for_file(vf, vf.read_text(), _AWS_REPO_STYLE_ROOT)
    assert any("missing required_providers.aws" in e for e in errs)


_MISMATCHED_VERSIONS_TF = """\
terraform {
  required_providers {
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "~> 2.12"
    }
  }
  required_version = ">= 1.9"
}
"""


def test_errors_for_file_exception_skips_provider_version_check(tmp_path: Path) -> None:
    vf = tmp_path / "versions.tf"
    vf.write_text(_MISMATCHED_VERSIONS_TF, encoding="utf-8")
    errs = _errors_for_file(
        vf,
        vf.read_text(),
        _CLUSTER_ROOT,
        provider_version_exceptions=frozenset({vf.resolve()}),
    )
    assert errs == []


def test_errors_for_file_no_exception_still_rejects_version_mismatch(tmp_path: Path) -> None:
    vf = tmp_path / "versions.tf"
    vf.write_text(_MISMATCHED_VERSIONS_TF, encoding="utf-8")
    errs = _errors_for_file(vf, vf.read_text(), _CLUSTER_ROOT)
    assert any("must match root" in e for e in errs)


_EXAMPLES_YAML = """\
examples_readme:
  readme_template: docs/example_readme.md
  versions_tf:
    skip_if_name_contains: ["cluster destruction"]
    generate_when_missing_only: false
    force_generate: false
tables:
  - name: Examples
    example_rows:
      - folder_name: special
        name: Special Cluster Destruction Example
      - folder_name: other
        name: Basic Example
"""


def _write_examples_yaml(tmp_path: Path, content: str = _EXAMPLES_YAML) -> None:
    (tmp_path / "docs").mkdir(exist_ok=True)
    (tmp_path / "docs" / "examples.yaml").write_text(content, encoding="utf-8")


def test_load_provider_version_exceptions_skips_matched_example(tmp_path: Path) -> None:
    _write_examples_yaml(tmp_path)
    special_dir = tmp_path / "examples" / "special"
    special_dir.mkdir(parents=True)
    (special_dir / "versions.tf").write_text(_MISMATCHED_VERSIONS_TF, encoding="utf-8")

    exceptions = _load_provider_version_exceptions(tmp_path)
    assert (special_dir / "versions.tf").resolve() in exceptions
    assert (tmp_path / "examples" / "other" / "versions.tf").resolve() not in exceptions


def test_load_provider_version_exceptions_missing_file(tmp_path: Path) -> None:
    assert _load_provider_version_exceptions(tmp_path) == frozenset()


def test_load_provider_version_exceptions_empty_skip_list(tmp_path: Path) -> None:
    _write_examples_yaml(
        tmp_path,
        """\
examples_readme:
  readme_template: docs/example_readme.md
  versions_tf:
    skip_if_name_contains: []
    generate_when_missing_only: false
    force_generate: false
tables:
  - name: Examples
    example_rows:
      - folder_name: special
        name: Special Cluster Destruction Example
""",
    )
    special_dir = tmp_path / "examples" / "special"
    special_dir.mkdir(parents=True)
    (special_dir / "versions.tf").write_text(_MISMATCHED_VERSIONS_TF, encoding="utf-8")
    assert _load_provider_version_exceptions(tmp_path) == frozenset()


def test_validate_repo_respects_examples_yaml_exception(tmp_path: Path) -> None:
    (tmp_path / "versions.tf").write_text(
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
""",
        encoding="utf-8",
    )
    ex_dir = tmp_path / "examples" / "special"
    ex_dir.mkdir(parents=True)
    (ex_dir / "versions.tf").write_text(_MISMATCHED_VERSIONS_TF, encoding="utf-8")
    _write_examples_yaml(tmp_path)
    assert validate_repo(tmp_path) == []
