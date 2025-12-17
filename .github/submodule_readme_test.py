from __future__ import annotations

import submodule_readme as mod


def test_transform_submodule_source_without_version() -> None:
    content = """```hcl
module "cluster_import" {
  source = "../../modules/cluster_import"
  cluster_name = "test"
}
```"""
    result = mod.transform_submodule_source(
        content, "terraform-mongodbatlas-modules/cluster/mongodbatlas", "cluster_import"
    )
    assert (
        'source  = "terraform-mongodbatlas-modules/cluster/mongodbatlas//modules/cluster_import"'
        in result
    )
    assert "version" not in result


def test_transform_submodule_source_with_version() -> None:
    content = """```hcl
module "cluster_import" {
  source = "../../modules/cluster_import"
  cluster_name = "test"
}
```"""
    result = mod.transform_submodule_source(
        content,
        "terraform-mongodbatlas-modules/cluster/mongodbatlas",
        "cluster_import",
        "v0.2.0",
    )
    assert (
        'source  = "terraform-mongodbatlas-modules/cluster/mongodbatlas//modules/cluster_import"'
        in result
    )
    assert 'version = "0.2.0"' in result


def test_transform_submodule_source_multiple_occurrences() -> None:
    content = """First block:
```hcl
module "cluster_import" {
  source = "../../modules/cluster_import"
}
```

Second block:
```hcl
module "cluster_import" {
  for_each = {}
  source = "../../modules/cluster_import"
}
```"""
    result = mod.transform_submodule_source(
        content, "owner/module/provider", "cluster_import", "v1.0.0"
    )
    assert (
        result.count('source  = "owner/module/provider//modules/cluster_import"') == 2
    )
    assert result.count('version = "1.0.0"') == 2
