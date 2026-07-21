from pathlib import Path

import pytest

from workspace import gen, models, plan, run


@pytest.mark.parametrize("provider_version", ["2.2.0", None])
def test_provider_version_environment_controls_override_during_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    provider_version: str | None,
):
    override_path = tmp_path / plan.PROVIDER_VERSION_OVERRIDE_FILE
    if provider_version is None:
        monkeypatch.delenv(run.PROVIDER_VERSION_ENV, raising=False)
    else:
        monkeypatch.setenv(run.PROVIDER_VERSION_ENV, provider_version)
    monkeypatch.setattr(models, "resolve_workspaces", lambda *_: [tmp_path])
    monkeypatch.setattr(gen, "process_workspace", lambda *_, **__: None)
    monkeypatch.setattr(run, "_resolve_example_dirs", lambda *_: [])
    monkeypatch.setattr(plan, "run_terraform_plan", lambda *_, **__: None)

    def assert_override_state(_: Path):
        if provider_version is None:
            assert not override_path.exists()
        else:
            assert f'version = "= {provider_version}"' in override_path.read_text()

    monkeypatch.setattr(plan, "run_terraform_init", assert_override_state)

    run.main(
        mode=run.RunMode.PLAN_ONLY,
        include_examples="all",
        auto_approve=False,
        skip_init=False,
        ws="all",
        tests_dir=tmp_path,
        var_file=[],
        force_regen=False,
        show_uncovered=False,
    )

    assert not override_path.exists()
