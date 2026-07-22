from __future__ import annotations

import pytest

from workspace import models
from workspace.import_validation import (
    IMPORTS_GENERATED_TF,
    SKIP_SENTINEL,
    TFSTATE_FILE,
    StateResource,
    _diff_attributes,
    assert_clean_plan,
    assert_import_plan,
    assert_no_destroys,
    backup_and_restore_state,
    extract_import_id,
    extract_state_resources,
    generate_import_blocks_tf,
    resolve_import_entries,
    validate_atlas_types,
)

MAPPING = {
    "mongodbatlas_encryption_at_rest": "{project_id}",
    "mongodbatlas_cloud_provider_access_setup": "{project_id}-{role_id}-AWS",
    "mongodbatlas_privatelink_endpoint": "{project_id}-{private_link_id}-AWS-{region}",
    "mongodbatlas_log_integration": SKIP_SENTINEL,
}


def test_extract_import_id_atlas_type():
    attrs = {"project_id": "p1", "role_id": "r1"}
    result = extract_import_id("mongodbatlas_cloud_provider_access_setup", attrs, MAPPING)
    assert result == "p1-r1-AWS"


def test_extract_import_id_non_atlas():
    assert extract_import_id("aws_kms_key", {"id": "123"}, MAPPING) is None


def test_extract_import_id_skip():
    assert extract_import_id("mongodbatlas_log_integration", {}, MAPPING) is None


def test_resolve_import_entries_missing_state_address():
    example = models.Example(
        name="enc",
        plan_regressions=[
            models.PlanRegression(address="mongodbatlas_encryption_at_rest.this"),
        ],
        import_validation=models.ImportValidationConfig(enabled=True),
    )
    with pytest.raises(ValueError, match="missing from state"):
        resolve_import_entries(
            [example],
            {
                "module.ex_other.mongodbatlas_encryption_at_rest.this": StateResource(
                    address="module.ex_other.mongodbatlas_encryption_at_rest.this",
                    resource_type="mongodbatlas_encryption_at_rest",
                    values={"project_id": "p1"},
                )
            },
            MAPPING,
        )


def test_validate_atlas_types_missing():
    with pytest.raises(ValueError, match="mongodbatlas_new_resource"):
        validate_atlas_types({"mongodbatlas_new_resource"}, MAPPING)


def test_validate_atlas_types_ok():
    validate_atlas_types({"mongodbatlas_encryption_at_rest"}, MAPPING)


def test_generate_import_blocks_tf():
    entries = [
        ("module.ex_enc.mongodbatlas_encryption_at_rest.this", "proj-123"),
        ("module.ex_enc.mongodbatlas_cloud_provider_access_setup.this", "proj-123-role-1-AWS"),
    ]
    result = generate_import_blocks_tf(entries)
    assert "to = module.ex_enc.mongodbatlas_encryption_at_rest.this" in result
    assert 'id = "proj-123"' in result
    assert 'id = "proj-123-role-1-AWS"' in result
    assert result.count("import {") == 2


def test_extract_state_resources():
    state = {
        "values": {
            "root_module": {
                "resources": [
                    {"address": "aws_kms_key.this", "type": "aws_kms_key", "values": {"id": "k1"}},
                ],
                "child_modules": [
                    {
                        "resources": [
                            {
                                "address": "module.ex_enc.mongodbatlas_encryption_at_rest.this",
                                "type": "mongodbatlas_encryption_at_rest",
                                "values": {"project_id": "p1"},
                            }
                        ],
                        "child_modules": [],
                    }
                ],
            }
        }
    }
    resources = extract_state_resources(state)
    assert "aws_kms_key.this" in resources
    assert (
        resources["module.ex_enc.mongodbatlas_encryption_at_rest.this"].resource_type
        == "mongodbatlas_encryption_at_rest"
    )


def _make_rc(
    address: str,
    actions: list[str],
    importing: bool = False,
    before: dict | None = None,
    after: dict | None = None,
    after_unknown: dict | None = None,
) -> dict:
    change: dict = {"actions": actions, "before": before or {}, "after": after or {}}
    if after_unknown:
        change["after_unknown"] = after_unknown
    if importing:
        # TF 1.13+ stores importing under change (legacy top-level kept for coverage)
        change["importing"] = {"id": "some-id"}
    return {"address": address, "change": change}


def _make_example(
    name: str, known_changes: list[models.ImportKnownChange] | None = None
) -> models.Example:
    return models.Example(
        name=name,
        import_validation=models.ImportValidationConfig(
            enabled=True,
            known_changes=known_changes or [],
        ),
    )


def test_assert_import_plan_clean():
    plan_json = {
        "resource_changes": [
            _make_rc(
                "module.ex_enc.mongodbatlas_encryption_at_rest.this", ["no-op"], importing=True
            ),
        ]
    }
    assert assert_import_plan(plan_json, _make_example("enc")) == []


def test_assert_import_plan_unexpected_create():
    plan_json = {
        "resource_changes": [
            _make_rc("module.ex_enc.mongodbatlas_encryption_at_rest.this", ["create"]),
        ]
    }
    failures = assert_import_plan(plan_json, _make_example("enc"))
    assert len(failures) == 1
    assert "unexpected actions" in failures[0]


def test_assert_import_plan_known_change():
    kc = models.ImportKnownChange(
        address="mongodbatlas_encryption_at_rest.this",
        actions=["update"],
        changed_attributes=["project_id"],
    )
    plan_json = {
        "resource_changes": [
            _make_rc(
                "module.ex_enc.mongodbatlas_encryption_at_rest.this",
                ["update"],
                importing=True,
                before={"project_id": "old"},
                after={"project_id": "new"},
            ),
        ]
    }
    assert assert_import_plan(plan_json, _make_example("enc", [kc])) == []


def test_assert_import_plan_attribute_mismatch():
    kc = models.ImportKnownChange(
        address="mongodbatlas_encryption_at_rest.this",
        actions=["update"],
        changed_attributes=["project_id"],
    )
    plan_json = {
        "resource_changes": [
            _make_rc(
                "module.ex_enc.mongodbatlas_encryption_at_rest.this",
                ["update"],
                importing=True,
                before={"project_id": "old", "name": "a"},
                after={"project_id": "new", "name": "b"},
            ),
        ]
    }
    failures = assert_import_plan(plan_json, _make_example("enc", [kc]))
    assert len(failures) == 1
    assert "expected changed_attributes" in failures[0]


def test_assert_import_plan_wildcard_known_change():
    kc = models.ImportKnownChange(
        address="mongodbatlas_encryption_at_rest.this",
        actions=["update"],
        changed_attributes=[],
    )
    plan_json = {
        "resource_changes": [
            _make_rc(
                "module.ex_enc.mongodbatlas_encryption_at_rest.this",
                ["update"],
                importing=True,
                before={"project_id": "old", "name": "a"},
                after={"project_id": "new", "name": "b"},
            ),
        ]
    }
    assert assert_import_plan(plan_json, _make_example("enc", [kc])) == []


def test_assert_import_plan_non_importing_update():
    plan_json = {
        "resource_changes": [
            _make_rc(
                "module.ex_enc.mongodbatlas_encryption_at_rest.this",
                ["update"],
                importing=False,
                before={"project_id": "old"},
                after={"project_id": "new"},
            ),
        ]
    }
    failures = assert_import_plan(plan_json, _make_example("enc"))
    assert len(failures) == 1
    assert "non-import change" in failures[0]
    assert "changed: ['project_id']" in failures[0]


def test_assert_import_plan_legacy_top_level_importing():
    """TF <=1.12 put importing on the resource_change object."""
    plan_json = {
        "resource_changes": [
            {
                "address": "module.ex_enc.mongodbatlas_encryption_at_rest.this",
                "importing": {"id": "legacy"},
                "change": {
                    "actions": ["update"],
                    "before": {"project_id": "old"},
                    "after": {"project_id": "new"},
                },
            }
        ]
    }
    failures = assert_import_plan(plan_json, _make_example("enc"))
    assert len(failures) == 1
    assert "import drift" in failures[0]
    assert "changed: ['project_id']" in failures[0]


def test_assert_import_plan_data_source_read_auto_skipped():
    plan_json = {
        "resource_changes": [
            _make_rc(
                "module.ex_enc.module.encryption_private_endpoint.data.mongodbatlas_encryption_at_rest_private_endpoint.this",
                ["read"],
                importing=False,
            ),
        ]
    }
    assert assert_import_plan(plan_json, _make_example("enc")) == []


def test_assert_import_plan_non_importing_known_change():
    kc = models.ImportKnownChange(
        address="module.encryption_private_endpoint.mongodbatlas_encryption_at_rest_private_endpoint.this",
        actions=["update"],
        changed_attributes=["status", "timeouts"],
    )
    plan_json = {
        "resource_changes": [
            _make_rc(
                "module.ex_enc.module.encryption_private_endpoint.mongodbatlas_encryption_at_rest_private_endpoint.this",
                ["update"],
                importing=False,
                before={"status": "ACTIVE"},
                after={"status": "PENDING", "timeouts": {"create": "30m"}},
            ),
        ]
    }
    assert assert_import_plan(plan_json, _make_example("enc", [kc])) == []


def test_assert_import_plan_actions_mismatch():
    kc = models.ImportKnownChange(
        address="mongodbatlas_encryption_at_rest.this",
        actions=["no-op"],
        changed_attributes=[],
    )
    plan_json = {
        "resource_changes": [
            _make_rc(
                "module.ex_enc.mongodbatlas_encryption_at_rest.this",
                ["update"],
                importing=True,
                before={"project_id": "old"},
                after={"project_id": "new"},
            ),
        ]
    }
    failures = assert_import_plan(plan_json, _make_example("enc", [kc]))
    assert len(failures) == 1
    assert "expected actions" in failures[0]


def test_assert_no_destroys_clean():
    plan_json = {
        "resource_changes": [
            _make_rc("module.ex_enc.mongodbatlas_encryption_at_rest.this", ["no-op"]),
            _make_rc("module.ex_enc.aws_kms_key.this", ["update"]),
        ]
    }
    assert assert_no_destroys(plan_json) == []


def test_assert_no_destroys_with_deletes():
    plan_json = {
        "resource_changes": [
            _make_rc("module.ex_enc.mongodbatlas_encryption_at_rest.this", ["no-op"]),
            _make_rc("module.ex_other.aws_kms_key.atlas", ["delete"]),
            _make_rc("module.ex_other.aws_iam_role.this", ["create", "delete"]),
        ]
    }
    result = assert_no_destroys(plan_json)
    assert len(result) == 2
    assert "module.ex_other.aws_kms_key.atlas" in result
    assert "module.ex_other.aws_iam_role.this" in result


def test_assert_clean_plan_all_noop():
    plan_json = {
        "resource_changes": [
            _make_rc("module.ex_enc.mongodbatlas_encryption_at_rest.this", ["no-op"]),
            _make_rc("module.ex_enc.aws_kms_key.this", ["no-op"]),
        ]
    }
    assert assert_clean_plan(plan_json, _make_example("enc")) == []


def test_assert_clean_plan_unexpected_change():
    plan_json = {
        "resource_changes": [
            _make_rc("module.ex_enc.mongodbatlas_encryption_at_rest.this", ["update"]),
        ]
    }
    failures = assert_clean_plan(plan_json, _make_example("enc"))
    assert len(failures) == 1
    assert "expected no-op after apply" in failures[0]


def test_assert_clean_plan_known_change_allowed():
    kc = models.ImportKnownChange(
        address="mongodbatlas_encryption_at_rest.this",
        actions=["update"],
        changed_attributes=["project_id"],
    )
    plan_json = {
        "resource_changes": [
            _make_rc(
                "module.ex_enc.mongodbatlas_encryption_at_rest.this",
                ["update"],
                before={"project_id": "old"},
                after={"project_id": "new"},
            ),
        ]
    }
    assert assert_clean_plan(plan_json, _make_example("enc", [kc])) == []


def test_assert_import_plan_after_unknown_excluded():
    kc = models.ImportKnownChange(
        address="mongodbatlas_encryption_at_rest_private_endpoint.this",
        actions=["update"],
        changed_attributes=["timeouts"],
    )
    plan_json = {
        "resource_changes": [
            _make_rc(
                "module.ex_enc.mongodbatlas_encryption_at_rest_private_endpoint.this",
                ["update"],
                importing=True,
                before={"status": "ACTIVE", "id": "abc"},
                after={"status": None, "id": None, "timeouts": {"create": "30m"}},
                after_unknown={"status": True, "id": True},
            ),
        ]
    }
    assert assert_import_plan(plan_json, _make_example("enc", [kc])) == []


def test_extract_import_id_missing_attribute():
    with pytest.raises(KeyError, match="mongodbatlas_encryption_at_rest.*missing_attr"):
        extract_import_id(
            "mongodbatlas_encryption_at_rest",
            {"other_field": "val"},
            {"mongodbatlas_encryption_at_rest": "{missing_attr}"},
        )


def test_backup_and_restore_state_happy_path(tmp_path):
    tfstate = tmp_path / TFSTATE_FILE
    tfstate.write_text('{"version": 4}')
    with backup_and_restore_state(tmp_path):
        tfstate.write_text('{"version": 4, "modified": true}')
    assert tfstate.read_text() == '{"version": 4}'
    assert not (tmp_path / f"{TFSTATE_FILE}.import-backup").exists()
    assert not (tmp_path / IMPORTS_GENERATED_TF).exists()


def test_backup_and_restore_state_missing_tfstate(tmp_path):
    with pytest.raises(ValueError, match="terraform.tfstate not found"):
        with backup_and_restore_state(tmp_path):
            pass


def test_backup_and_restore_state_restores_on_exception(tmp_path):
    tfstate = tmp_path / TFSTATE_FILE
    original = '{"version": 4}'
    tfstate.write_text(original)
    imports_tf = tmp_path / IMPORTS_GENERATED_TF
    with pytest.raises(RuntimeError, match="simulated"):
        with backup_and_restore_state(tmp_path):
            tfstate.write_text("corrupted")
            imports_tf.write_text("import {}")
            raise RuntimeError("simulated")
    assert tfstate.read_text() == original
    assert not (tmp_path / f"{TFSTATE_FILE}.import-backup").exists()
    assert not imports_tf.exists()


def test_diff_attributes_key_only_in_before():
    change = {"before": {"removed": "val"}, "after": {}}
    assert _diff_attributes(change) == {"removed"}


def test_diff_attributes_key_only_in_after():
    change = {"before": {}, "after": {"added": "val"}}
    assert _diff_attributes(change) == {"added"}


def test_diff_attributes_after_unknown_excluded():
    change = {
        "before": {"status": "ACTIVE", "name": "a"},
        "after": {"status": None, "name": "b"},
        "after_unknown": {"status": True},
    }
    result = _diff_attributes(change)
    assert "status" not in result
    assert "name" in result


def test_diff_attributes_empty_after_unknown_dict_not_excluded():
    """Terraform uses after_unknown: {tags: {}} when tags itself is known."""
    change = {
        "before": {"tags": None},
        "after": {"tags": {}},
        "after_unknown": {"tags": {}},
    }
    assert _diff_attributes(change) == {"tags"}


def test_diff_attributes_nested_after_unknown_compares_known_portions():
    # known leaf differs under nested marker -> report top-level key
    assert _diff_attributes(
        {
            "before": {"replication_specs": [{"a": 1}]},
            "after": {"replication_specs": [{"a": 2}]},
            "after_unknown": {"replication_specs": [{"disk_iops": True}]},
        }
    ) == {"replication_specs"}
    # project limits: concrete blocks vs [], only computed leaves unknown
    assert _diff_attributes(
        {
            "before": {"limits": []},
            "after": {"limits": [{"name": "openDownloadBytes", "value": 42}]},
            "after_unknown": {
                "limits": [{"current_usage": True, "default_limit": True, "maximum_limit": True}]
            },
        }
    ) == {"limits"}
    # only unknown leaf differs -> ignore
    assert (
        _diff_attributes(
            {
                "before": {"replication_specs": [{"a": 1, "disk_iops": None}]},
                "after": {"replication_specs": [{"a": 1, "disk_iops": 3000}]},
                "after_unknown": {"replication_specs": [{"disk_iops": True}]},
            }
        )
        == set()
    )


def test_assert_clean_plan_known_change_actions_mismatch():
    kc = models.ImportKnownChange(
        address="mongodbatlas_encryption_at_rest.this",
        actions=["no-op"],
        changed_attributes=[],
    )
    plan_json = {
        "resource_changes": [
            _make_rc(
                "module.ex_enc.mongodbatlas_encryption_at_rest.this",
                ["update"],
                before={"project_id": "old"},
                after={"project_id": "new"},
            ),
        ]
    }
    failures = assert_clean_plan(plan_json, _make_example("enc", [kc]))
    assert len(failures) == 1
    assert "expected actions" in failures[0]
