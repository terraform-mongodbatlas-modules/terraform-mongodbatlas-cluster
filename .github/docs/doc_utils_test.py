from __future__ import annotations

from docs import doc_utils
from docs.config_loader import SkipRule


def test_apply_template_vars_replaces_placeholders() -> None:
    content = "Hello {{ .NAME }}, welcome to {{ .PROJECT }}!"
    template_vars = {"name": "World", "project": "Terraform"}
    result = doc_utils.apply_template_vars(content, template_vars)
    assert result == "Hello World, welcome to Terraform!"


def test_apply_template_vars_empty_value_removes_line() -> None:
    content = """\
Line 1
{{ .EMPTY_VAR }}
Line 3"""
    template_vars = {"empty_var": ""}
    result = doc_utils.apply_template_vars(content, template_vars)
    assert result == "Line 1\nLine 3"


def test_apply_template_vars_missing_var_removes_line() -> None:
    content = """\
Before
{{ .MISSING }}
After"""
    result = doc_utils.apply_template_vars(content, {})
    assert result == "Before\nAfter"


def test_apply_template_vars_preserves_lines_without_placeholders() -> None:
    content = """\
No placeholders here
Just regular content
# With some formatting"""
    result = doc_utils.apply_template_vars(content, {})
    assert result == content


def test_apply_template_vars_skip_rules_development() -> None:
    content = "{{ .PRODUCTION_CONSIDERATIONS }}"
    template_vars = {"production_considerations": "Production stuff"}
    skip_rules = [
        SkipRule(
            context_pattern="development",
            skip_vars=[
                "production_considerations",
                "production_considerations_comment",
            ],
        )
    ]
    # Using "development" context with skip rule should skip production vars
    result = doc_utils.apply_template_vars(
        content,
        template_vars,
        context_name="Development Cluster",
        skip_rules=skip_rules,
    )
    assert result == ""


def test_apply_template_vars_skip_rules_no_match() -> None:
    content = "{{ .PRODUCTION_CONSIDERATIONS }}"
    template_vars = {"production_considerations": "Production stuff"}
    skip_rules = [
        SkipRule(
            context_pattern="development",
            skip_vars=["production_considerations"],
        )
    ]
    # Using "production" context should NOT skip production vars
    result = doc_utils.apply_template_vars(
        content,
        template_vars,
        context_name="Production Cluster",
        skip_rules=skip_rules,
    )
    assert result == "Production stuff"


def test_apply_template_vars_root_context_applies_all() -> None:
    content = "{{ .PRODUCTION_CONSIDERATIONS }}"
    template_vars = {"production_considerations": "Production stuff"}
    skip_rules = [
        SkipRule(
            context_pattern="development",
            skip_vars=["production_considerations"],
        )
    ]
    # Root context should apply all vars (doesn't match "development" pattern)
    result = doc_utils.apply_template_vars(
        content,
        template_vars,
        context_name="root",
        skip_rules=skip_rules,
    )
    assert result == "Production stuff"


def test_should_skip_template_var_no_rules() -> None:
    assert not doc_utils.should_skip_template_var("any", "production_var", None)
    assert not doc_utils.should_skip_template_var("any", "production_var", [])


def test_should_skip_template_var_development_skips_listed_vars() -> None:
    skip_rules = [
        SkipRule(
            context_pattern="development",
            skip_vars=["production_considerations", "production_comment"],
        )
    ]
    assert doc_utils.should_skip_template_var(
        "Development Cluster", "production_considerations", skip_rules
    )
    assert doc_utils.should_skip_template_var(
        "08_development_cluster", "production_comment", skip_rules
    )


def test_should_skip_template_var_unlisted_var_not_skipped() -> None:
    skip_rules = [
        SkipRule(
            context_pattern="development",
            skip_vars=["production_considerations"],
        )
    ]
    # Even with matching pattern, vars not in skip_vars are not skipped
    assert not doc_utils.should_skip_template_var(
        "Development Cluster", "some_other_var", skip_rules
    )


def test_should_skip_template_var_case_insensitive_context() -> None:
    skip_rules = [
        SkipRule(
            context_pattern="development",
            skip_vars=["production_var"],
        )
    ]
    assert doc_utils.should_skip_template_var("DEVELOPMENT", "production_var", skip_rules)
    skip_rules_upper = [
        SkipRule(
            context_pattern="DEVELOPMENT",
            skip_vars=["production_var"],
        )
    ]
    assert doc_utils.should_skip_template_var("development", "production_var", skip_rules_upper)
