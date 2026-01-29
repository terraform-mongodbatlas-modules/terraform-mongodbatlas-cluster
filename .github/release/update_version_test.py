"""Tests for update_version module."""

from __future__ import annotations

import textwrap
from pathlib import Path

from release import update_version as mod


def _dedent(s: str) -> str:
    return textwrap.dedent(s).lstrip("\n")


def test_update_versions_tf_adds_provider_meta(tmp_path: Path, capsys) -> None:
    versions_tf = tmp_path / "versions.tf"
    versions_tf.write_text(
        _dedent("""
            terraform {
              required_providers {
                mongodbatlas = {
                  source  = "mongodb/mongodbatlas"
                }
              }
            }
            """),
        encoding="utf-8",
    )

    mod.update_versions_tf(versions_tf, "1.0.0", "versions.tf", "cluster")

    content = versions_tf.read_text(encoding="utf-8")
    assert 'provider_meta "mongodbatlas"' in content
    assert 'module_name    = "cluster"' in content
    assert 'module_version = "1.0.0"' in content
    assert "ok Added provider_meta" in capsys.readouterr().out


def test_update_versions_tf_skips_non_mongodbatlas(tmp_path: Path, capsys) -> None:
    versions_tf = tmp_path / "versions.tf"
    original = 'terraform { required_providers { aws = { source = "hashicorp/aws" } } }'
    versions_tf.write_text(original, encoding="utf-8")

    mod.update_versions_tf(versions_tf, "1.0.0", "versions.tf", "cluster")

    assert versions_tf.read_text(encoding="utf-8") == original
    assert "Skipped" in capsys.readouterr().out


def test_main_end_to_end(tmp_path: Path) -> None:
    # Root with provider_meta
    root_versions = tmp_path / "versions.tf"
    root_versions.write_text(
        _dedent("""
            terraform {
              required_providers {
                mongodbatlas = { source  = "mongodb/mongodbatlas" }
              }
              provider_meta "mongodbatlas" {
                module_name    = "test-module"
                module_version = "local"
              }
            }
            """),
        encoding="utf-8",
    )

    # Submodule without provider_meta
    submodule_dir = tmp_path / "modules" / "sub"
    submodule_dir.mkdir(parents=True)
    submodule_versions = submodule_dir / "versions.tf"
    submodule_versions.write_text(
        _dedent("""
            terraform {
              required_providers {
                mongodbatlas = { source  = "mongodb/mongodbatlas" }
              }
            }
            """),
        encoding="utf-8",
    )

    # Non-mongodbatlas file (should be skipped)
    other_dir = tmp_path / "other"
    other_dir.mkdir()
    other_versions = other_dir / "versions.tf"
    other_versions.write_text("terraform { }", encoding="utf-8")

    # Run update
    version = mod.extract_version_number("v1.5.0")
    module_name = mod.get_module_name_from_root(tmp_path)
    for version_file in tmp_path.rglob("versions.tf"):
        mod.update_versions_tf(
            version_file, version, str(version_file.relative_to(tmp_path)), module_name
        )

    # Verify root updated
    assert 'module_version = "1.5.0"' in root_versions.read_text(encoding="utf-8")

    # Verify submodule got provider_meta added
    submodule_content = submodule_versions.read_text(encoding="utf-8")
    assert 'provider_meta "mongodbatlas"' in submodule_content
    assert 'module_name    = "test-module"' in submodule_content
    assert 'module_version = "1.5.0"' in submodule_content

    # Verify non-mongodbatlas skipped
    assert "provider_meta" not in other_versions.read_text(encoding="utf-8")


def test_inject_provider_meta_with_blocks_after_terraform() -> None:
    """Test that provider_meta is injected in terraform block, not after other blocks."""
    content = _dedent("""
        terraform {
          required_providers {
            mongodbatlas = {
              source  = "mongodb/mongodbatlas"
            }
          }
        }

        resource "mongodbatlas_project" "example" {
          name = "test"
        }
        """)

    result = mod.inject_provider_meta(content, "cluster", "1.0.0")

    assert result is not None
    # Check that provider_meta appears before resource block (inside terraform block)
    provider_meta_pos = result.find('provider_meta "mongodbatlas"')
    resource_pos = result.find('resource "mongodbatlas_project"')
    assert provider_meta_pos < resource_pos, "provider_meta should be before resource block"
    assert 'module_name    = "cluster"' in result
    assert 'module_version = "1.0.0"' in result


def test_inject_provider_meta_no_terraform_block() -> None:
    """Test that injection fails gracefully when no terraform block exists."""
    content = _dedent("""
        resource "mongodbatlas_project" "example" {
          name = "test"
        }
        """)

    result = mod.inject_provider_meta(content, "cluster", "1.0.0")

    assert result is None


def test_inject_provider_meta_malformed_no_closing_brace() -> None:
    """Test that injection fails gracefully when terraform block is malformed."""
    content = "terraform {"  # Missing closing brace

    result = mod.inject_provider_meta(content, "cluster", "1.0.0")

    assert result is None


def test_update_versions_tf_warns_on_malformed_file(tmp_path: Path, capsys) -> None:
    """Test that a warning is printed when terraform block is malformed."""
    versions_tf = tmp_path / "versions.tf"
    original = 'mongodbatlas = { source = "mongodb/mongodbatlas" }'  # No terraform block
    versions_tf.write_text(original, encoding="utf-8")

    mod.update_versions_tf(versions_tf, "1.0.0", "versions.tf", "cluster")

    # File should be unchanged
    assert versions_tf.read_text(encoding="utf-8") == original
    # Warning should be printed
    stderr = capsys.readouterr().err
    assert "Could not find terraform block" in stderr
