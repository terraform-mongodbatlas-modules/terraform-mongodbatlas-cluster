"""Tests for tf_registry_source module."""

from __future__ import annotations

import pytest

from release import tf_registry_source as mod

CLUSTER_REMOTE = (
    "https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster.git"
)
OVERRIDE = "terraform-mongodbatlas-modules/atlas-aws-chatbot/mongodbatlas"


@pytest.fixture
def cluster_remote(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TF_REGISTRY_SOURCE", raising=False)
    monkeypatch.setattr(mod, "get_git_remote_url", lambda: CLUSTER_REMOTE)


def test_override_is_used_for_registry_source_and_module_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TF_REGISTRY_SOURCE", OVERRIDE)
    monkeypatch.setattr(mod, "get_git_remote_url", lambda: pytest.fail("remote should not be read"))

    assert mod.get_registry_source() == OVERRIDE
    assert mod.get_module_name() == "atlas_aws_chatbot"


def test_main_prints_override(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    monkeypatch.setenv("TF_REGISTRY_SOURCE", OVERRIDE)

    mod.main()

    assert capsys.readouterr().out.strip() == OVERRIDE


def test_remote_derived_values_unchanged_without_override(
    cluster_remote: None,
) -> None:
    assert mod.get_registry_source() == "terraform-mongodbatlas-modules/cluster/mongodbatlas"
    assert mod.get_module_name() == "cluster"


def test_remote_derived_values_unchanged_for_atlas_prefix(
    cluster_remote: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        mod,
        "get_git_remote_url",
        lambda: (
            "https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-atlas-gcp.git"
        ),
    )

    assert mod.get_registry_source() == "terraform-mongodbatlas-modules/atlas-gcp/mongodbatlas"
    assert mod.get_module_name() == "atlas_gcp"
