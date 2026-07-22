from __future__ import annotations

from docs import submodule_readme as mod

_REGISTRY = "terraform-mongodbatlas-modules/cluster/mongodbatlas"
_SUB = "cloud_backup_schedule"
_REL = f"../../modules/{_SUB}"
_ABS = f"{_REGISTRY}//modules/{_SUB}"


def test_transform_submodule_source_without_version() -> None:
    content = f"""```hcl
module "{_SUB}" {{
  source = "{_REL}"
  project_id = "proj"
}}
```"""
    result = mod.transform_submodule_source(content, _REGISTRY, _SUB)
    assert f'source  = "{_ABS}"' in result
    assert "version" not in result


def test_transform_submodule_source_with_version() -> None:
    content = f"""```hcl
module "{_SUB}" {{
  source = "{_REL}"
  project_id = "proj"
}}
```"""
    result = mod.transform_submodule_source(content, _REGISTRY, _SUB, "v0.2.0")
    assert f'source  = "{_ABS}"' in result
    assert 'version = "0.2.0"' in result


def test_transform_submodule_source_multiple_occurrences() -> None:
    content = f"""First block:
```hcl
module "{_SUB}" {{
  source = "{_REL}"
}}
```

Second block:
```hcl
module "{_SUB}" {{
  for_each = {{}}
  source = "{_REL}"
}}
```"""
    result = mod.transform_submodule_source(content, "owner/module/provider", _SUB, "v1.0.0")
    assert result.count(f'source  = "owner/module/provider//modules/{_SUB}"') == 2
    assert result.count('version = "1.0.0"') == 2
