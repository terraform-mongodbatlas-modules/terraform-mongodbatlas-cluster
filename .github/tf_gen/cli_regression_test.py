from __future__ import annotations

from pathlib import Path

import pytest

from tf_gen.cli import generate_for_config
from tf_gen.conftest import DEFAULT_PROVIDERS

MODULE_CONFIGS = ["project", "aws", "azure", "gcp"]


@pytest.mark.parametrize("module_name", MODULE_CONFIGS)
def test_cli_module_regression(
    module_name: str,
    cli_regression_dir: Path,
    file_regression,
):
    """Regression test for module gen.yaml configs (project, aws, azure, gcp)."""
    config_path = cli_regression_dir / module_name / "gen.yaml"
    dest_path = cli_regression_dir / module_name
    results = generate_for_config(
        config_path,
        dest_path=dest_path,
        dry_run=True,
        provider_defaults=DEFAULT_PROVIDERS,
        cache_dir=cli_regression_dir / "schema_cache",
    )
    for filepath, content in sorted(results.items()):
        file_regression.check(content, fullpath=Path(filepath))
