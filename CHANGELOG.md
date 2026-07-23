## (Unreleased)

BREAKING CHANGES:

* submodule/cloud_backup_schedule: Manages the `cloud_backup_schedule` resource automatically when `backup_enabled` is `true` and `backup_mode` is not `UNMANAGED`, adding a new resource for existing clusters on next apply ([#169](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/pull/169))

NOTES:

* provider/mongodbatlas: Requires minimum version 2.12 for `mongodbatlas_cloud_backup_schedule` `skip_destroy` support ([#184](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/pull/184))
* terraform: Requires minimum version 1.10 ([#171](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/pull/171))

ENHANCEMENTS:

* example: Adds a "Cluster with Scheduled Backups" example demonstrating retention overrides, cross-region copy, and `backup_schedule_skip_destroy` ([#169](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/pull/169))
* module: Adds `backup_mode`, `backup_copy_region`, `backup_schedule_skip_destroy`, `backup_retention`, and `backup_export` variables for first-class backup schedule configuration ([#169](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/pull/169))

## 0.3.1 (March 17, 2026)

BUG FIXES:

* module: Wraps trimspace calls with try() to prevent crash on TF 1.9-1.11 when zone_name is null ([#128](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/pull/128))

## 0.3.0 (January 28, 2026)

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
