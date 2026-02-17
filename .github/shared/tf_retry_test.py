from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from shared import tf_retry
from shared.tf_retry import TerraformInitError, run_terraform_init

MODULE = run_terraform_init.__module__


def _make_result(returncode: int, stderr: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout="", stderr=stderr)


def test_success_no_retry(tmp_path: Path):
    with patch(f"{MODULE}.subprocess.run", return_value=_make_result(0)) as mock_run:
        result = run_terraform_init(["terraform", "init"], tmp_path)
    assert result.returncode == 0
    assert mock_run.call_count == 1


def test_transient_error_retries_then_succeeds(tmp_path: Path):
    checksum_err = "does not match any of the checksums recorded in the dependency lock file"
    side_effects = [
        _make_result(1, stderr=checksum_err),
        _make_result(0),
    ]
    with (
        patch(f"{MODULE}.subprocess.run", side_effect=side_effects),
        patch.object(tf_retry.run_terraform_init.retry, "wait", return_value=0),  # pyright: ignore[reportFunctionMemberAccess]
    ):
        result = run_terraform_init(["terraform", "init"], tmp_path)
    assert result.returncode == 0


def test_non_transient_error_no_retry(tmp_path: Path):
    with (
        patch(
            f"{MODULE}.subprocess.run",
            return_value=_make_result(1, stderr="Invalid provider configuration"),
        ) as mock_run,
        pytest.raises(TerraformInitError, match="Invalid provider configuration"),
    ):
        run_terraform_init(["terraform", "init"], tmp_path)
    assert mock_run.call_count == 1


def test_non_checksum_transient_error_retries(tmp_path: Path):
    registry_err = "registry service is unreachable"
    side_effects = [
        _make_result(1, stderr=registry_err),
        _make_result(0),
    ]
    with (
        patch(f"{MODULE}.subprocess.run", side_effect=side_effects),
        patch.object(tf_retry.run_terraform_init.retry, "wait", return_value=0),  # pyright: ignore[reportFunctionMemberAccess]
    ):
        result = run_terraform_init(["terraform", "init"], tmp_path)
    assert result.returncode == 0


def test_checksum_error_cleans_cache(tmp_path: Path):
    providers_dir = tmp_path / ".terraform" / "providers"
    providers_dir.mkdir(parents=True)
    (providers_dir / "dummy").write_text("stale")
    modules_dir = tmp_path / ".terraform" / "modules"
    modules_dir.mkdir(parents=True)
    (modules_dir / "mod").write_text("stale")

    checksum_err = "does not match any of the checksums recorded in the dependency lock file"
    side_effects = [
        _make_result(1, stderr=checksum_err),
        _make_result(0),
    ]
    with (
        patch(f"{MODULE}.subprocess.run", side_effect=side_effects),
        patch.object(tf_retry.run_terraform_init.retry, "wait", return_value=0),  # pyright: ignore[reportFunctionMemberAccess]
    ):
        run_terraform_init(["terraform", "init"], tmp_path)
    assert not providers_dir.exists()
    assert not modules_dir.exists()
