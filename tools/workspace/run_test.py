from pathlib import Path

import pytest
import typer

from workspace import gen, models, plan, run


def test_provider_version_environment_controls_override_during_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    provider_version = "2.2.0"
    override_path = tmp_path / plan.PROVIDER_VERSION_OVERRIDE_FILE
    monkeypatch.setenv(run.PROVIDER_VERSION_ENV, provider_version)
    monkeypatch.setattr(models, "resolve_workspaces", lambda *_: [tmp_path])
    monkeypatch.setattr(gen, "process_workspace", lambda *_, **__: None)
    monkeypatch.setattr(run, "_resolve_example_dirs", lambda *_: [])
    monkeypatch.setattr(plan, "run_terraform_plan", lambda *_, **__: None)

    def assert_override_state(_: Path):
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


@pytest.mark.parametrize("provider_version", ["~> 2.2", "   "])
def test_provider_version_error_is_reported(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    provider_version: str,
):
    monkeypatch.setenv(run.PROVIDER_VERSION_ENV, provider_version)
    monkeypatch.setattr(models, "resolve_workspaces", lambda *_: [tmp_path])
    monkeypatch.setattr(gen, "process_workspace", lambda *_, **__: None)
    monkeypatch.setattr(run, "_resolve_example_dirs", lambda *_: [])

    with pytest.raises(typer.Exit) as exc_info:
        run.main(
            mode=run.RunMode.PLAN_ONLY,
            include_examples="all",
            auto_approve=False,
            skip_init=True,
            ws="all",
            tests_dir=tmp_path,
            var_file=[],
            force_regen=False,
            show_uncovered=False,
        )

    assert exc_info.value.exit_code == 1
    assert f"Error: Invalid exact provider version {provider_version!r}" in capsys.readouterr().err
