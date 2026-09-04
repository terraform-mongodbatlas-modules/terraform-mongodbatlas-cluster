## (Unreleased)

BUG FIXES:

* module: Rejects analytics-only or read-only-only regions listed before electable regions ([#218](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/pull/218))
* module: Sets `priority` to 0 on analytics-only and read-only-only regions ([#218](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/pull/218))

## 0.4.0 (July 29, 2026)

BREAKING CHANGES:

* submodule/cloud_backup_schedule: Manages the `cloud_backup_schedule` resource automatically when `backup_enabled` is `true` and `backup_mode` is not `UNMANAGED`, adding a new resource for existing clusters on next apply ([#169](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/pull/169))
* submodule/cluster_import: Removes the experimental `cluster_import` submodule ([#185](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/pull/185))
* variable/advanced_configuration: Changes recommended default value for `minimum_enabled_tls_protocol` from `TLS1_2` to `TLS1_3` under `default_feature_set = "RECOMMENDED"`. To leave `minimum_enabled_tls_protocol` unset, set `default_feature_set` to `"STANDARD"`. To pin a TLS value for a zero-diff upgrade, explicitly set `minimum_enabled_tls_protocol` to the desired TLS value (see docs/v0.4.0-upgrade-guide.md) ([#181](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/pull/181))
* variable/config_server_management_mode: Defaults to `ATLAS_MANAGED` instead of `null`. To keep a dedicated config server, set to `FIXED_TO_DEDICATED` ([#186](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/pull/186))
* variable/tags: Defaults to `null` instead of `{}` so imported clusters without tags do not plan an empty-map update ([#187](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/pull/187))

NOTES:

* example: Removes the `13_example_import` example ([#185](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/pull/185))
* example: Updates 02_production_cluster_with_manual_scaling to a symmetric sharded topology: `instance_size` is now set once at the root level (`M40` for all shards) instead of per-shard sizes (`M40`/`M30` via Independent Shard Scaling). Per-shard sizing was dropped from the example due to known provider topology-change limitations on asymmetric sharded clusters ([#202](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/pull/202))
* provider/mongodbatlas: Requires minimum version 2.12 for `mongodbatlas_cloud_backup_schedule` `skip_destroy` support ([#184](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/pull/184))
* terraform: Requires minimum version 1.10 ([#171](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/pull/171))
* variable/regions: Deprecates `shard_number` in favor of `shard_name` (removal in v1), first-appearance group order unchanged while still in use ([#190](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/pull/190))

ENHANCEMENTS:

* example: Adds a "Cluster with Scheduled Backups" example demonstrating retention overrides, cross-region copy, and `backup_schedule_skip_destroy` ([#169](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/pull/169))
* module: Adds `backup_mode`, `backup_copy_region`, `backup_schedule_skip_destroy`, `backup_retention`, and `backup_export` variables for first-class backup schedule configuration ([#169](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/pull/169))
* variable/default_feature_set: Adds `RECOMMENDED` and `STANDARD` modes so future module defaults can opt in or opt out of plan changes on minor upgrades ([#181](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/pull/181))
* variable/regions: Adds `shard_name` for `SHARDED`/`GEOSHARDED` grouping (`^[a-z0-9]{1,24}$`). Orders named shards by first appearance in `regions` ([#190](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/pull/190))
* variable/version_release_system: Rejects `CONTINUOUS` when `mongo_db_major_version` is set ([#183](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/pull/183))

BUG FIXES:

* module: Clamps auto-scaling `instance_size` (electable, read-only, analytics) to the configured min/max when an existing cluster is outside that range ([#145](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/pull/145))

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
