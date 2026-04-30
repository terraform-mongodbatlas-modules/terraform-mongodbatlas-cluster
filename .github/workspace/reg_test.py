from __future__ import annotations

from workspace import models, reg


def test_filter_values_omits_null_for_redact_attr():
    out = reg.filter_values(
        {"password": None, "name": "x"},
        skip_attrs=[],
        skip_values=["null"],
        redact_attrs=["password"],
    )
    assert "password" not in out
    assert out == {"name": "x"}


def test_filter_values_redacts_non_null_redact_attr():
    out = reg.filter_values(
        {"password": "secret"},
        skip_attrs=[],
        skip_values=["null"],
        redact_attrs=["password"],
    )
    assert out == {"password": "<password>"}


def test_filter_values_nested_omits_null_redact():
    out = reg.filter_values(
        {"block": {"password": None, "id": "1"}},
        skip_attrs=[],
        skip_values=["null"],
        redact_attrs=["password"],
    )
    assert out == {"block": {"id": "1"}}


def test_dump_resource_yaml_omits_null_default_redact_password():
    values = {"password": None, "visible": "ok"}
    config = models.WsConfig(examples=[], var_groups={})
    example = models.Example(number=1)
    dump = models.DumpConfig(
        skip_lines=models.SkipLines(
            substring_attributes=[],
            substring_values=[],
            redact_attributes=[],
            use_default_redact=True,
        )
    )
    yaml_out = reg.dump_resource_yaml(values, config, example, dump)
    assert "password" not in yaml_out
    assert "visible" in yaml_out
    assert "ok" in yaml_out
