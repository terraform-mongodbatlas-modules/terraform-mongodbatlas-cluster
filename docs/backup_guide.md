# MongoDB Atlas Cluster Backup Guide

This guide explains how to configure and manage backups in the MongoDB Atlas Terraform Cluster Module: schedule defaults, point-in-time restore recommendations, deletion behavior, and how to export snapshots using the other Landing Zone modules.

## Table of Contents

- [Introduction](#introduction)
- [Recommendations Summary](#recommendations-summary)
- [Backup Modes](#backup-modes)
- [Schedule Defaults](#schedule-defaults)
- [`pit_enabled` and `backup_enabled` Recommendations](#pit_enabled-and-backup_enabled-recommendations)
- [Cross-Region Copy](#cross-region-copy)
- [Exporting Snapshots (Other LZ Modules)](#exporting-snapshots-other-lz-modules)
- [Deletion Behavior](#deletion-behavior)
- [Key Variables Reference](#key-variables-reference)
- [Additional Resources](#additional-resources)

## Introduction

The module manages the `mongodbatlas_cloud_backup_schedule` resource for you as a first-class capability, you no longer need a separate `mongodbatlas_cloud_backup_schedule` resource block alongside the cluster. `backup_mode` controls whether and how the module manages this resource; `backup_retention`, `backup_copy_region`, `backup_export`, and `backup_schedule_skip_destroy` configure it.

See [`examples/14_cluster_with_backup_schedule`](../examples/14_cluster_with_backup_schedule) for a complete working example combining retention overrides, cross-region copy, and deletion behavior.

## Recommendations Summary

| Scenario | `backup_enabled` | `pit_enabled` | `backup_mode` |
| --- | --- | --- | --- |
| Production | `true` (default) | `null` (default: `true`) | `SCHEDULED` (default) |
| Dev/non-production, still want some coverage | `true` (default) | `false` or default | `ON_DEMAND` |
| Backup Compliance Policy enabled | `true` | default | `SCHEDULED`, `backup_schedule_skip_destroy = true` |
| Migrating off module-managed backups | -- | -- | Two-apply `UNMANAGED` migration, see [Deletion Behavior](#deletion-behavior) |

## Backup Modes

`backup_mode` (default `"SCHEDULED"`) has three values:

- **`SCHEDULED`**: module-managed frequency policies (`hourly`/`daily`/`weekly`/`monthly`/`yearly`). This is what most users want.
- **`ON_DEMAND`**: the schedule resource is still created, but all frequency-based policy items are removed. Only manual (on-demand) snapshots and PIT (if enabled) are covered. Use this when you want to trigger snapshots yourself rather than on a recurring schedule.
- **`UNMANAGED`**: the module does not create the schedule resource at all. You manage `mongodbatlas_cloud_backup_schedule` yourself with a standalone resource. `backup_copy_region`, `backup_retention`, and `backup_export` must be left at their defaults in this mode; see [Deletion Behavior](#deletion-behavior) for the migration path.

`backup_mode` is ignored (no effect, no error) when `backup_enabled = false`. The module never creates the schedule resource in that case, regardless of `backup_mode`.

## Schedule Defaults

Each frequency (`hourly`/`daily`/`weekly`/`monthly`/`yearly`) in `backup_retention` is optional. When a frequency is provided, `retention_value` is required; `frequency_interval`/`retention_unit` fall back to the Atlas UI default for that frequency if omitted. When a frequency is omitted and `skip_default_retentions = false` (the default), the module creates it using the same defaults as the Atlas UI:

| Frequency | `frequency_interval` | `retention_unit` | `retention_value` |
| --- | --- | --- | --- |
| `hourly`  | 6  | `days`   | 7  |
| `daily`   | 1 (fixed) | `days`   | 7  |
| `weekly`  | 6  | `weeks`  | 4  |
| `monthly` | 40 | `months` | 12 |
| `yearly`  | 12 | `years`  | 1  |

Set `skip_default_retentions = true` to only create the frequencies you explicitly declare. Any frequency you don't list is omitted entirely, not just defaulted.

```hcl
backup_retention = {
  daily = { retention_value = 30 } # override the 7-day default; hourly/weekly/monthly/yearly keep their defaults
}
```

`reference_hour_of_day`/`reference_minute_of_hour` control the UTC snapshot window (default: cluster creation time), and `restore_window_days` controls the PIT restore window. `restore_window_days` cannot exceed the `hourly` policy's `retention_value` (in days), this is your effective RPO (how far back you can restore). See [Configure the Restore Window](https://www.mongodb.com/docs/atlas/backup/cloud-backup/configure-backup-policy/#configure-the-restore-window) for details. `ondemand` is accepted for shape-compatibility with the project module's future `backup_compliance_policy.retention`, but has no corresponding field on `mongodbatlas_cloud_backup_schedule` and is ignored.

**`ON_DEMAND` and frequency fields:** setting `backup_retention`'s frequency fields (`hourly`/`daily`/`weekly`/`monthly`/`yearly`) is rejected (validation error at `terraform plan`) when `backup_mode = "ON_DEMAND"`, since that mode removes all frequency policies. `restore_window_days` and `ondemand` remain valid there.

**Caveat: NVMe tiers:** the `hourly` default above (6 hours) matches Atlas's documented default for standard tiers, but Atlas documents a 12-hour default for NVMe tiers. The module does not currently derive the default from the cluster's effective instance tier, so NVMe users who want the Atlas-recommended interval should set `backup_retention.hourly.frequency_interval = 12` explicitly.

## `pit_enabled` and `backup_enabled` Recommendations

`pit_enabled` (continuous backup / point-in-time restore) defaults to the value of `backup_enabled` when left `null`, so by default, enabling backups also enables PIT. You can override it explicitly in either direction, except you cannot set `pit_enabled = true` when `backup_enabled = false` (PIT requires Cloud Backup).

**Recommendation:** leave both at their defaults (`backup_enabled = true`, `pit_enabled = null`) for production clusters. `backup_enabled` is an Atlas Architecture Center recommended default; leaving `pit_enabled` at its default enables continuous backup alongside it, giving you the finest-grained restore window available.

**Atlas requires an `hourly` policy item for Continuous Cloud Backup.** If `backup_mode = "SCHEDULED"` and PIT is effectively enabled, omitting the `hourly` frequency (via `skip_default_retentions = true` with `hourly` unset) is rejected at `terraform plan`, since Atlas rejects that combination at the API level. If you don't need PIT, set `pit_enabled = false` explicitly to omit `hourly`.

**Dev/non-production clusters** that don't need scheduled backups at all can use `backup_mode = "ON_DEMAND"` instead of `backup_enabled = false`. This keeps manual snapshots and PIT available (cheaper than full scheduled backups) without disabling backup coverage entirely. See [`examples/08_development_cluster`](../examples/08_development_cluster) for this pattern.

## Cross-Region Copy

Cross-region copy protects your snapshots against a regional outage: if the primary region becomes unavailable, you can still restore from the copy in the secondary region. It's also useful for data-residency requirements that call for backups to exist in a specific secondary region.

`backup_copy_region` replicates scheduled and on-demand snapshots to a target region (multi-region snapshot distribution):

```hcl
backup_copy_region = {} # auto-derive the secondary region from var.regions
```

- **`region`**: when omitted (`backup_copy_region = {}`), the module auto-derives a secondary region from `var.regions` (the highest-priority region after the primary), so the copy target stays valid across regional failovers without a config change. Requires at least 2 regions in `var.regions`; fails validation otherwise. Not derived from `var.replication_specs`, set `region` explicitly when using that variable.
- **`cloud_provider`**: override for multi-cloud clusters (default: derived from the target region, or left for the provider to infer if it can't be resolved).
- **`should_copy_oplogs`**: copies oplogs for point-in-time restore from the copy region (default: `true` if PIT is enabled).

**`GEOSHARDED` clusters** get one cluster-wide copy target derived from the first zone's regions, per-zone copy targets are not supported. The module also sends the created cluster's `zone_id` for that same first zone, matching the zone `region`/`cloud_provider` are derived from. The underlying Atlas API disambiguates copy targets by zone, so this is needed on multi-zone clusters even though the provider itself marks `zone_id` optional.

Setting `backup_copy_region` is rejected (validation error) when `backup_mode = "UNMANAGED"` or `backup_enabled = false`.

## Exporting Snapshots (Other LZ Modules)

`backup_export` exports snapshots to a cloud storage bucket. The bucket itself is **not** managed by this module, it's managed by the corresponding CSP Landing Zone module (`atlas-aws`, `atlas-azure`, `atlas-gcp`), which each expose a dedicated `export_bucket_id` output built for exactly this purpose.

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

## Deletion Behavior

`backup_schedule_skip_destroy` maps directly to the provider's `skip_destroy` on the `mongodbatlas_cloud_backup_schedule` resource:

- **`false`** (default): deletes the schedule (the recurring policy that creates new snapshots and governs retention) on destroy. This does **not** delete snapshots that already exist, those remain until their own previously-assigned retention expires; no new scheduled snapshots are created afterward.
- **`true`**: no-op on destroy; the schedule resource is removed from Terraform state only, and the schedule itself (including future snapshot creation) is left intact in Atlas. Use this when a Backup Compliance Policy is enabled on the project.

**Migrating to `UNMANAGED` requires two applies** if you want to preserve the existing schedule/snapshots:

1. First apply: set `backup_schedule_skip_destroy = true` while `backup_mode` is still `SCHEDULED`/`ON_DEMAND`.
2. Second apply: switch `backup_mode` to `UNMANAGED`.

Setting both in the same apply does **not** skip the delete, Terraform still destroys the resource (`skip_destroy` only takes effect if the resource already exists with that setting applied in a prior state).

`retain_backups_enabled` is a separate, cluster-level flag (not part of the backup schedule resource) that controls whether existing backup snapshots are retained when the *cluster itself* is deleted. Recommended `true` for production clusters.

## Key Variables Reference

| Variable | Purpose |
| --- | --- |
| `backup_enabled` | Whether the cluster can perform backups at all (production default: `true`) |
| `pit_enabled` | Continuous backup / point-in-time restore (defaults to `backup_enabled`) |
| `backup_mode` | `SCHEDULED` / `ON_DEMAND` / `UNMANAGED`. See [Backup Modes](#backup-modes) |
| `backup_retention` | Per-frequency retention overrides. See [Schedule Defaults](#schedule-defaults) |
| `backup_copy_region` | Cross-region snapshot copy target. See [Cross-Region Copy](#cross-region-copy) |
| `backup_export` | Export snapshots to a CSP bucket. See [Exporting Snapshots](#exporting-snapshots-other-lz-modules) |
| `backup_schedule_skip_destroy` | Deletion behavior on destroy. See [Deletion Behavior](#deletion-behavior) |
| `retain_backups_enabled` | Retain snapshots when the cluster itself is deleted |

See the [main README](../README.md#backup-schedule) for the full generated variable reference, including types and defaults.

## Additional Resources

- **[Main Module README](../README.md#backup-schedule)**: Complete generated variable documentation for the Backup Schedule section
- **[`examples/14_cluster_with_backup_schedule`](../examples/14_cluster_with_backup_schedule)**: Complete working example
- **[`examples/08_development_cluster`](../examples/08_development_cluster)**: `ON_DEMAND` mode for dev clusters
- **[Atlas Configure Backup Policy Documentation](https://www.mongodb.com/docs/atlas/backup/cloud-backup/configure-backup-policy/)**: Official Atlas backup policy documentation, including PIT restore window constraints
- **[`mongodbatlas_cloud_backup_schedule` Provider Documentation](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs/resources/cloud_backup_schedule)**: Complete resource schema reference

---

**Questions or feedback?** Please open an issue in the [GitHub repository](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/issues).
