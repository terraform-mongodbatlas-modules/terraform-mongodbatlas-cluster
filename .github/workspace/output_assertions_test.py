from __future__ import annotations

from workspace import models, output_assertions


def _config_with_assertions(
    example_id: str, assertions: list[models.OutputAssertion]
) -> models.WsConfig:
    return models.WsConfig(
        examples=[models.Example(name=example_id, output_assertions=assertions)],
        var_groups={},
    )


def test_extract_example_outputs():
    raw = {
        "ex_backup": {"value": {"bucket_id": "abc123"}, "type": ["object"]},
        "ex_enc": {"value": {"key": "xyz"}},
        "unrelated": {"value": "ignored"},
    }
    result = output_assertions._extract_example_outputs(raw)
    assert result == {"backup": {"bucket_id": "abc123"}, "enc": {"key": "xyz"}}


def test_pattern_match_pass():
    raw = {"ex_test": {"value": {"bucket_id": "abc123def456"}}}
    config = _config_with_assertions(
        "test", [models.OutputAssertion(output="bucket_id", pattern=r"^[a-f0-9]{12}$")]
    )
    assert output_assertions.run_output_assertions(config, raw)


def test_pattern_match_fail():
    raw = {"ex_test": {"value": {"bucket_id": "NOT-HEX"}}}
    config = _config_with_assertions(
        "test", [models.OutputAssertion(output="bucket_id", pattern=r"^[a-f0-9]{12}$")]
    )
    assert not output_assertions.run_output_assertions(config, raw)


def test_not_empty_pass():
    raw = {"ex_test": {"value": {"name": "my-cluster"}}}
    config = _config_with_assertions(
        "test", [models.OutputAssertion(output="name", not_empty=True)]
    )
    assert output_assertions.run_output_assertions(config, raw)


def test_not_empty_fail_none():
    raw = {"ex_test": {"value": {"name": None}}}
    config = _config_with_assertions(
        "test", [models.OutputAssertion(output="name", not_empty=True)]
    )
    assert not output_assertions.run_output_assertions(config, raw)


def test_not_empty_fail_missing_key():
    raw = {"ex_test": {"value": {}}}
    config = _config_with_assertions(
        "test", [models.OutputAssertion(output="missing", not_empty=True)]
    )
    assert not output_assertions.run_output_assertions(config, raw)


def test_no_assertions_returns_true():
    config = models.WsConfig(
        examples=[models.Example(name="test")],
        var_groups={},
    )
    assert output_assertions.run_output_assertions(config, {})
