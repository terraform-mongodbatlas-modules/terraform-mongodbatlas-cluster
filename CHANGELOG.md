## (Unreleased)

ENHANCEMENTS:

* variable/pit_enabled: Auto-disable when `backup_enabled=false`, add validation for invalid config: `pit_enabled=true`, `backup_enabled=false` ([#78](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/pull/78))

## 0.2.0 (December 17, 2025)

ENHANCEMENTS:

* example/11_module_wrapper_cluster_size: Simplifies cluster_wrapper example by consolidating regions_helper module logic into a single comprehensive module ([#40](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/pull/40))
* module: Adds support for auto-scaling inheritance from electable nodes to analytics nodes when no explicit analytics auto-scaling is configured ([#45](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/pull/45))

BUG FIXES:

* terraform: Fixes short-circuit evaluation bug in auto_scaling validation for Terraform 1.9-1.11 ([#52](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/pull/52))
* terraform: Fixes variable validation compatibility with Terraform 1.9-1.11 by wrapping floor() checks with try() for null safety ([#46](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/pull/46))
* variable/regions: Fixes validation errors when using replication_specs instead of regions ([#44](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/pull/44))

## 0.1.0 (October 31, 2025)

NOTES:

* module: Initial version
