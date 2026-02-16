from __future__ import annotations

from pathlib import Path

import pytest

from workspace import gen, models


@pytest.fixture()
def fake_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    examples_dir = tmp_path / gen.EXAMPLES_DIR_NAME
    examples_dir.mkdir()
    monkeypatch.setattr(models, "REPO_ROOT", tmp_path)
    return examples_dir


def test_generate_modules_tf_includes_output_blocks(fake_repo: Path, tmp_path: Path):
    (fake_repo / "backup_export").mkdir()
    config = models.WsConfig(
        examples=[models.Example(name="backup_export")],
        var_groups={},
    )
    result = gen.generate_modules_tf(config, config.examples, tmp_path)
    assert result is not None
    assert 'module "ex_backup_export" {' in result
    assert 'output "ex_backup_export" {' in result
    assert "value = module.ex_backup_export" in result


def test_generate_modules_tf_output_per_example(fake_repo: Path, tmp_path: Path):
    (fake_repo / "01_basic").mkdir()
    (fake_repo / "02_advanced").mkdir()
    config = models.WsConfig(
        examples=[models.Example(number=1), models.Example(number=2)],
        var_groups={},
    )
    result = gen.generate_modules_tf(config, config.examples, tmp_path)
    assert result is not None
    assert 'output "ex_01" {' in result
    assert 'output "ex_02" {' in result
    assert "value = module.ex_01" in result
    assert "value = module.ex_02" in result


def test_generate_modules_tf_empty_examples(tmp_path: Path):
    config = models.WsConfig(examples=[], var_groups={})
    assert gen.generate_modules_tf(config, [], tmp_path) is None
