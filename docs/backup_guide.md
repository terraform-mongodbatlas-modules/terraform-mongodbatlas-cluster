# MongoDB Atlas Cluster Backup Guide

This guide explains how to configure and manage Cloud Backup in the MongoDB Atlas Terraform Cluster Module, including backup schedule configuration and defaults, point-in-time restore recommendations, snapshot export through the companion Landing Zone modules (`atlas-aws`, `atlas-azure`, `atlas-gcp`), and deletion behavior.

## Table of Contents

- [Introduction](#introduction)
- [Recommendations Summary](#recommendations-summary)
- [Backup Modes](#backup-modes)
- [Backup Schedule Configuration and Defaults](#backup-schedule-configuration-and-defaults)
- [`pit_enabled` and `backup_enabled` Recommendations](#pit_enabled-and-backup_enabled-recommendations)
- [Cross-Region Copy](#cross-region-copy)
- [Exporting Snapshots (Other LZ Modules)](#exporting-snapshots-other-lz-modules)
- [Restoring from a Snapshot](#restoring-from-a-snapshot)
- [Deletion Behavior](#deletion-behavior)
- [Key Variables Reference](#key-variables-reference)
- [Additional Resources](#additional-resources)

## Introduction

The module manages the `mongodbatlas_cloud_backup_schedule` resource for you as a first-class resource, so you don't need to declare a separate resource block alongside the cluster. `backup_mode` controls whether and how the module manages the resource, and backup_retention, backup_copy_region, backup_export, and backup_schedule_skip_destroy configure the backup policy.

See [`examples/14_cluster_with_backup_schedule`](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.4.1/examples/14_cluster_with_backup_schedule) for a complete working example combining retention overrides, cross-region copy, and deletion behavior.

## Recommendations Summary

| Scenario | `backup_enabled` | `pit_enabled` | `backup_mode` |
| --- | --- | --- | --- |
| Production | `true` (default) | `null` (default: `true`) | `SCHEDULED` (default) |
| Dev/non-production, still want some coverage | `true` (default) | `false` or default | `ON_DEMAND` |
| Backup Compliance Policy enabled | `true` | default | `SCHEDULED`, `backup_schedule_skip_destroy = true` |
| Migrating off module-managed backups | -- | -- | Two-apply `UNMANAGED` migration, see [Deletion Behavior](#deletion-behavior) |

## Backup Modes

`backup_mode` (default `"SCHEDULED"`) has three values:

- **`SCHEDULED`**: the module creates the `mongodbatlas_cloud_backup_schedule` resource and manages the cluster's backup policy for you. It applies a default policy (`hourly`/`daily`/`weekly`/`monthly`/`yearly`) unless you override it through `backup_retention`. This is what most users want.
- **`ON_DEMAND`**: the module creates the `mongodbatlas_cloud_backup_schedule` resource but removes all default frequency policy items (`hourly`/`daily`/`weekly`/`monthly`/`yearly`) and rejects any backup policy configuration through `backup_retention`. Only on-demand snapshots and point-in-time restores are available; PIT restore always needs an on-demand snapshot to exist before your target time to serve as the base for oplog replay, so PIT has nothing to restore from until you trigger at least one. Use this when you want to trigger snapshots yourself instead of on a recurring schedule.
- **`UNMANAGED`**: the module does not create the `mongodbatlas_cloud_backup_schedule` resource. You manage it yourself with a standalone `mongodbatlas_cloud_backup_schedule` resource. `backup_copy_region`, `backup_retention`, and `backup_export` must be left at their defaults in this mode. See [Deletion Behavior](#deletion-behavior) for the migration path from a module-managed mode.

`backup_mode` is ignored (no effect, no error) when `backup_enabled = false`. The module never creates the `mongodbatlas_cloud_backup_schedule` resource in that case, regardless of `backup_mode`.

## Backup Schedule Configuration and Defaults

You can use this module to manage scheduled backup snapshots by setting `backup_mode = "SCHEDULED"` (the default) and defining custom retention values per frequency in `backup_retention`. `backup_retention` is optional; the module falls back to a pre-configured schedule when it's omitted.

### Default Retention Values

When `backup_mode = "SCHEDULED"` and `skip_default_retentions = false` (the default), the module creates a backup policy using the same defaults as the Atlas UI:

| Frequency | `frequency_interval` | `retention_unit` | `retention_value` |
| --- | --- | --- | --- |
| `hourly`  | 6  | `days`   | 7  |
| `daily`   | 1 (fixed) | `days`   | 7  |
| `weekly`  | 6  | `weeks`  | 4  |
| `monthly` | 40 | `months` | 12 |
| `yearly`  | 12 | `years`  | 1  |

### Overriding Defaults

Set the frequencies you want in `backup_retention` to override the defaults above. Declare a block for each frequency (`hourly`/`daily`/`weekly`/`monthly`/`yearly`) you want to customize; within each block, `retention_value` is required, and `frequency_interval`/`retention_unit` are optional and fall back to the defaults above when omitted:

```hcl
backup_retention = {
  daily = { retention_value = 30 } # override the 7-day default; hourly/weekly/monthly/yearly keep their defaults
}
```

`frequency_interval` means something different for each frequency:

| Frequency | `frequency_interval` accepts | Meaning |
| --- | --- | --- |
| `hourly`  | `1`, `2`, `4`, `6`, `8`, `12` (NVMe tiers: `12` only) | Hours between snapshots |
| `daily`   | `1` (fixed) | Once per day |
| `weekly`  | `1`-`7` | Day of the week (`1` = Monday, `7` = Sunday) |
| `monthly` | `1`-`28`, or `40` | Day of the month (`40` = last day) |
| `yearly`  | `1`-`12` | Month of the year, on the 1st (`1` = January, `12` = December) |

`retention_unit` accepts `days`, `weeks`, `months`, or `years`.

Set `skip_default_retentions = true` to create only the frequencies you explicitly declare; any frequency you don't list is then omitted entirely, not just defaulted:

```hcl
backup_retention = {
  skip_default_retentions = true
  daily   = { retention_value = 30 } # create daily only
  monthly = { retention_value = 6 }  # and monthly; no hourly/weekly/yearly
}
```

Frequency fields can't be set at all when `backup_mode = "ON_DEMAND"` (validation error at `terraform plan`), since that mode removes all frequency policies. See [Backup Modes](#backup-modes). `restore_window_days` and `ondemand` remain valid there. When point-in-time restore is effectively enabled, you also can't omit the `hourly` frequency. See [`pit_enabled` and `backup_enabled` Recommendations](#pit_enabled-and-backup_enabled-recommendations).

**Caveat: NVMe tiers.** The `hourly` default above (6 hours) matches Atlas's documented default for standard tiers; NVMe tiers only accept `frequency_interval = 12` for the `hourly` policy item (no other value is valid). The module does not currently derive this from the cluster's effective instance tier, so NVMe users must set `backup_retention.hourly.frequency_interval = 12` explicitly.

`reference_hour_of_day`/`reference_minute_of_hour` control the UTC snapshot window (default: `18:00` UTC per [Atlas's default backup policy](https://www.mongodb.com/docs/atlas/backup/cloud-backup/configure-backup-policy/#example) when left unset), and `restore_window_days` controls the PIT restore window. `restore_window_days` cannot exceed the `hourly` policy's `retention_value` (in days); this is your effective RPO (Recovery Point Objective: the maximum acceptable data loss, in time, if you need to restore). See [Configure the Restore Window](https://www.mongodb.com/docs/atlas/backup/cloud-backup/configure-backup-policy/#configure-the-restore-window) for details.

`ondemand` is accepted for shape-compatibility with the project module's future `backup_compliance_policy.retention`, but has no corresponding field on `mongodbatlas_cloud_backup_schedule` and is ignored.

## `pit_enabled` and `backup_enabled` Recommendations

`pit_enabled` (continuous backup / point-in-time restore) defaults to the value of `backup_enabled` when left `null`, so by default, enabling backups also enables PIT. You can override it explicitly in either direction, except you cannot set `pit_enabled = true` when `backup_enabled = false` (PIT requires Cloud Backup).

**Recommendation:** leave both at their defaults (`backup_enabled = true`, `pit_enabled = null`) for production clusters. `backup_enabled` is an Atlas Architecture Center recommended default; leaving `pit_enabled` at its default enables continuous backup alongside it, giving you the finest-grained restore window available. See [How Backups Support Disaster Recovery](https://www.mongodb.com/docs/atlas/architecture/current/disaster-recovery/#how-backups-support-disaster-recovery) for RPO/RTO guidance (RTO, Recovery Time Objective, is the maximum acceptable downtime before service is restored. For example, a "4 hour RTO" means back online within 4 hours).

**Atlas requires an `hourly` policy item for Continuous Cloud Backup.** If `backup_mode = "SCHEDULED"` and PIT is effectively enabled, omitting the `hourly` frequency (via `skip_default_retentions = true` with `hourly` unset) is rejected at `terraform plan`, since Atlas rejects that combination at the API level. If you don't need PIT, set `pit_enabled = false` explicitly to omit `hourly`.

**Dev/non-production clusters** that don't need scheduled backups at all can use `backup_mode = "ON_DEMAND"` instead of `backup_enabled = false`. This keeps manual snapshots and PIT available without disabling backup coverage entirely, but note that PIT (continuous backup) is billed separately regardless of `backup_mode`; set `pit_enabled = false` explicitly if you want to avoid that cost too. See [`examples/08_development_cluster`](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.4.1/examples/08_development_cluster) for this pattern.

## Cross-Region Copy

Cross-region copy protects your snapshots against a regional outage: if the primary region becomes unavailable, you can still restore from the copy in the secondary region. It's also useful for data-residency requirements that call for backups to exist in a specific secondary region.

`backup_copy_region` replicates scheduled and on-demand snapshots to a target region (multi-region snapshot distribution):

```hcl
backup_copy_region = {} # auto-derive the secondary region from var.regions
```

- **`region`**: when omitted (`backup_copy_region = {}`), the module auto-derives a secondary region from `var.regions` (the highest-priority region after the primary), so the copy target stays valid across regional failovers without a config change. Requires at least 2 regions in `var.regions`; fails validation otherwise. Not derived from `var.replication_specs`, so set `region` explicitly when using that variable.
- **`cloud_provider`**: override for multi-cloud clusters (default: derived from the target region, or left for the provider to infer if it can't be resolved).
- **`should_copy_oplogs`**: copies oplogs for point-in-time restore from the copy region (default: `true` if PIT is enabled).

**`GEOSHARDED` clusters** get one cluster-wide copy target derived from the first zone's regions. Per-zone copy targets are not supported. The module also sends the created cluster's `zone_id` for that same first zone, matching the zone `region`/`cloud_provider` are derived from. The underlying Atlas API disambiguates copy targets by zone, so this is needed on multi-zone clusters even though the provider itself marks `zone_id` optional.

Setting `backup_copy_region` is rejected (validation error) when `backup_mode = "UNMANAGED"` or `backup_enabled = false`.

## Exporting Snapshots (Other LZ Modules)

`backup_export` exports snapshots to a cloud storage bucket. The bucket itself is **not** managed by this module; it's managed by the corresponding CSP Landing Zone module (`atlas-aws`, `atlas-azure`, `atlas-gcp`), which each expose a dedicated `export_bucket_id` output built for exactly this purpose.

```hcl
module "atlas_aws" {
  source     = "terraform-mongodbatlas-modules/atlas-aws/mongodbatlas"
  project_id = var.project_id

  backup_export = {
    enabled          = true
    create_s3_bucket = { enabled = true }
  }
}

module "cluster" {
  source = "terraform-mongodbatlas-modules/cluster/mongodbatlas"
  # ...

  backup_export = {
    export_bucket_id = module.atlas_aws.export_bucket_id
    frequency_type   = "daily" # one of: daily, weekly, monthly, yearly
  }
}
```

The same pattern applies to `atlas-azure` (`create_storage_account`) and `atlas-gcp` (`create_gcs_bucket`), only the bucket-creation block differs; `export_bucket_id` is the integration point in all three.

Setting this hardcodes `auto_export_enabled = true` on the schedule; there is no independent toggle. Valid with `backup_mode = "ON_DEMAND"` (exports whatever snapshots exist). Rejected (validation error) when set together with `backup_mode = "UNMANAGED"` or `backup_enabled = false`.

## Restoring from a Snapshot

Restoring is not a module-managed operation: a restore is a one-off action, not a steady-state cluster configuration, so it isn't wrapped by this module. To restore from a snapshot, use the `mongodbatlas_cloud_backup_snapshot_restore_job` resource directly, alongside a module-managed cluster. See [Restore a Cluster from a Backup Snapshot](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.4.1/examples/15_restore_snapshot_to_cluster) for a full example covering the automated and point-in-time delivery types.

The resource supports three delivery types (set exactly one per restore job):

- **`automated`**: Atlas restores the snapshot directly onto a target cluster (`target_cluster_name`/`target_project_id`), which can be the same cluster it came from or a different one, in the same or a different project. This wipes all existing data on the target cluster before loading the snapshot.
- **`point_in_time`**: Atlas restores the closest snapshot to the specified point in time (`point_in_time_utc_seconds`, or `oplog_ts/oplog_inc`), and then replays the oplog forward to bring the data to that point in time. This wipes all existing data on the target cluster before loading the snapshot. Requires `pit_enabled` to be `true` on the source cluster (either by default when `backup_enabled = true`, or set explicitly with `pit_enabled = true`). See [`pit_enabled` and `backup_enabled` Recommendations](#pit_enabled-and-backup_enabled-recommendations) for details.
- **`download`**: Atlas doesn't modify any cluster. Atlas returns a `delivery_url` for a downloadable `.tar.gz` of the snapshot's raw data files. The `.tar.gz` expires after a time window. Use this to save snapshot data outside of Atlas to inspect, archive, or load into a self-hosted MongoDB.

See the provider's [`mongodbatlas_cloud_backup_snapshot_restore_job` resource documentation](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs/resources/cloud_backup_snapshot_restore_job) for the full attribute reference.

## Deletion Behavior

`backup_schedule_skip_destroy` maps directly to the provider's `skip_destroy` on the `mongodbatlas_cloud_backup_schedule` resource:

- **`false`** (default): deletes the schedule (the recurring policy that creates new snapshots and governs retention) on destroy. This does **not** delete snapshots that already exist; those remain until their own previously-assigned retention expires; no new scheduled snapshots are created afterward.
- **`true`**: no-op on destroy; the schedule resource is removed from Terraform state only, and the schedule itself (including future snapshot creation) is left intact in Atlas. Use this when a Backup Compliance Policy is enabled on the project.

**Migrating to `UNMANAGED` requires two applies** if you want to preserve the existing schedule/snapshots:

1. First apply: set `backup_schedule_skip_destroy = true` while `backup_mode` is still `SCHEDULED`/`ON_DEMAND`.
2. Second apply: switch `backup_mode` to `UNMANAGED`.

Setting both in the same apply does **not** skip the delete; Terraform still destroys the resource (`skip_destroy` only takes effect if the resource already exists with that setting applied in a prior state).

`retain_backups_enabled` is a separate, cluster-level flag (not part of the backup schedule resource) that controls whether existing backup snapshots are retained when the *cluster itself* is deleted. Recommended `true` for production clusters.

**Known limitation:** if you delete a cluster with `retain_backups_enabled = true` (retaining its backups), Atlas will not let you create a new cluster with the same name in that project afterward. Use a different name for the new cluster, or delete the retained backups first if you no longer need them before reusing the name.

## Key Variables Reference

| Variable | Purpose |
| --- | --- |
| `backup_enabled` | Whether the cluster can perform backups at all (production default: `true`) |
| `pit_enabled` | Continuous backup / point-in-time restore (defaults to `backup_enabled`) |
| `backup_mode` | `SCHEDULED` / `ON_DEMAND` / `UNMANAGED`. See [Backup Modes](#backup-modes) |
| `backup_retention` | Per-frequency retention overrides. See [Backup Schedule Configuration and Defaults](#backup-schedule-configuration-and-defaults) |
| `backup_copy_region` | Cross-region snapshot copy target. See [Cross-Region Copy](#cross-region-copy) |
| `backup_export` | Export snapshots to a CSP bucket. See [Exporting Snapshots](#exporting-snapshots-other-lz-modules) |
| `backup_schedule_skip_destroy` | Deletion behavior on destroy. See [Deletion Behavior](#deletion-behavior) |
| `retain_backups_enabled` | Retain snapshots when the cluster itself is deleted |

See the [main README](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.4.1/README.md#backup-schedule) for the full generated variable reference, including types and defaults.

## Additional Resources

- **[Main Module README](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.4.1/README.md#backup-schedule)**: Complete generated variable documentation for the Backup Schedule section
- **[`examples/14_cluster_with_backup_schedule`](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.4.1/examples/14_cluster_with_backup_schedule)**: Complete working example
- **[`examples/08_development_cluster`](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.4.1/examples/08_development_cluster)**: `ON_DEMAND` mode for dev clusters
- **[Atlas Configure Backup Policy Documentation](https://www.mongodb.com/docs/atlas/backup/cloud-backup/configure-backup-policy/)**: Official Atlas backup policy documentation, including PIT restore window constraints
- **[`mongodbatlas_cloud_backup_schedule` Provider Documentation](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs/resources/cloud_backup_schedule)**: Complete resource schema reference

---

**Questions or feedback?** Please open an issue in the [GitHub repository](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/issues).
