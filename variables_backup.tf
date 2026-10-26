variable "backup_mode" {
  description = <<-EOT
    Schedule mode for backup. Controls whether and how the module manages the `cloud_backup_schedule` resource.
    `backup_enabled` is a separate cluster-level flag; `backup_mode` is ignored when `backup_enabled = false`.
    - `ON_DEMAND`: schedule resource created but all frequency policies removed (PIT + manual snapshots only)
    - `SCHEDULED`: module-managed frequency policies (`hourly`/`daily`/`weekly`/`monthly`/`yearly`)
    - `UNMANAGED`: module does not create the schedule resource. Consumer manages `cloud_backup_schedule`
      externally using a standalone resource. `backup_copy_region`, `backup_retention`, and `backup_export` must
      be left at their defaults; `backup_schedule_skip_destroy` is still allowed.

    Migrating to `UNMANAGED` with `backup_schedule_skip_destroy = true` requires two applies: set it to `true`
    first while `backup_mode` is still `SCHEDULED`/`ON_DEMAND`, then switch to `UNMANAGED` in a second apply.
    Setting both in the same apply does not skip the delete. See the [Backup Guide](./docs/backup_guide.md)
    for the full deletion-workflow writeup.
  EOT
  type        = string
  default     = "SCHEDULED"

  validation {
    condition     = contains(["ON_DEMAND", "SCHEDULED", "UNMANAGED"], var.backup_mode)
    error_message = "backup_mode must be one of: ON_DEMAND, SCHEDULED, UNMANAGED."
  }
}

variable "backup_copy_region" {
  description = <<-EOT
    Cross-region snapshot copy settings (multi-region snapshot distribution). When set, the module creates one
    `copy_settings` entry per target to replicate scheduled and on-demand snapshots to secondary regions. When left
    unset, the common default, the module creates no copies; `backup_copy_region = {}` derives one target.

    Choose the targets with exactly one of the following (they are mutually exclusive):
    - `region_count`: derive that many targets from the highest-priority secondary regions in `var.regions`, in
      `regions` order. Defaults to `1` when unset. Rejected when it exceeds the number of available secondary
      regions. Set `0` to remove every copy target while keeping `copy_policy_items_enabled = true`: Atlas enables
      that flag one-way per cluster and rejects disabling it, so this is the only supported way to stop cross-region
      copying once a cluster has enabled copy policy items (removing `backup_copy_region` outright fails). See the
      [Backup Guide](./docs/backup_guide.md#cross-region-copy).
    - `regions`: name the targets explicitly as an ordered list of secondary region names. Each entry must be a
      secondary region in `var.regions` (never the primary), with no duplicates. On multi-cloud clusters, matching
      is by region name (first row wins), so a name the primary shares with another provider cannot be named here;
      see the [Backup Guide](./docs/backup_guide.md#cross-region-copy) limitations.
    - `region`: pin one Atlas region name.

    When none of the three is set (`backup_copy_region = {}`), the module auto-derives one secondary region from
    `var.regions`, which is the highest-priority region after the primary, so the copy target stays valid across regional
    failovers without a config change. Requires at least 2 regions in `var.regions`; fails validation otherwise.

    Each target uses exactly one copy mechanism:
    - `copy_policy_items` (the default) are derived from `backup_retention`, using each frequency's
      `copy_retention_value`.
    - `last_number_of_snapshots` (1-500) switches every target to count-based copies, keeping the last N copies
      with the retention of the source snapshot. It is mutually exclusive with `backup_retention[*].copy_retention_value`.

    Other fields:
    - `cloud_provider`: override for multi-cloud clusters. Defaults to the provider Atlas derives from the target
      region, or left for the provider to infer if it can't be resolved. One value applies to every target.
    - `should_copy_oplogs`: copy oplogs for point-in-time restore from the copy region. Defaults to `true` if PIT
      is enabled, or `false` if PIT is disabled. One value applies to every target.
    - `update_copy_snapshots`: apply retention changes for updated copy policy items to snapshot copies Atlas took
      previously.
    - `delete_copy_snapshots`: delete snapshot copies when their associated copy policy item is removed.

    See the [Backup Guide](./docs/backup_guide.md#cross-region-copy) for the one-way `copy_policy_items_enabled`
    switch, the retention ceiling, and the limitations (no per-target copy settings, no per-zone copy targets).
  EOT
  type = object({
    region                   = optional(string)
    regions                  = optional(list(string))
    region_count             = optional(number)
    cloud_provider           = optional(string)
    should_copy_oplogs       = optional(bool)
    last_number_of_snapshots = optional(number)
    update_copy_snapshots    = optional(bool)
    delete_copy_snapshots    = optional(bool)
  })
  nullable = true
  default  = null

  validation {
    condition     = var.backup_copy_region == null || (var.backup_mode != "UNMANAGED" && var.backup_enabled)
    error_message = "Cannot set backup_copy_region when backup_mode = \"UNMANAGED\" or backup_enabled = false."
  }

  validation {
    # try() per field -- a leading null-guard doesn't short-circuit here, see tests/plan_short_circuit.tftest.hcl.
    condition = var.backup_copy_region == null || length(compact([
      try(var.backup_copy_region.region, null) != null ? "region" : "",
      try(var.backup_copy_region.regions, null) != null ? "regions" : "",
      try(var.backup_copy_region.region_count, null) != null ? "region_count" : "",
    ])) <= 1
    error_message = "backup_copy_region: set at most one of region, regions, or region_count."
  }

  validation {
    # Ternary, not || -- || doesn't short-circuit on Terraform < 1.12 (see tests/plan_short_circuit.tftest.hcl),
    # so a plain "... == null || ... >= 0" would evaluate null >= 0 and fail planning when region_count is omitted.
    condition     = var.backup_copy_region == null || (try(var.backup_copy_region.region_count, null) == null ? true : var.backup_copy_region.region_count >= 0)
    error_message = "backup_copy_region.region_count must be at least 0."
  }

  validation {
    # Count-based copies and copy policy items are mutually exclusive on a copy setting.
    condition = var.backup_copy_region == null || try(var.backup_copy_region.last_number_of_snapshots, null) == null || alltrue([
      try(var.backup_retention.hourly.copy_retention_value, null) == null,
      try(var.backup_retention.daily.copy_retention_value, null) == null,
      try(var.backup_retention.weekly.copy_retention_value, null) == null,
      try(var.backup_retention.monthly.copy_retention_value, null) == null,
      try(var.backup_retention.yearly.copy_retention_value, null) == null,
    ])
    error_message = "backup_copy_region.last_number_of_snapshots (count-based copies) cannot be combined with backup_retention[*].copy_retention_value (copy policy items); they are mutually exclusive copy mechanisms."
  }
}

variable "backup_schedule_skip_destroy" {
  description = <<-EOT
    Maps directly to the provider's `skip_destroy` on the `cloud_backup_schedule` resource.
    - `false` (default): removes all backup schedule policies on destroy
    - `true`: no-op on destroy, resource removed from Terraform state only. Use when a Backup Compliance
      Policy is enabled. See `backup_mode`'s description for the `UNMANAGED` migration note.
  EOT
  type        = bool
  default     = false
}

variable "backup_retention" {
  description = <<-EOT
    Retention overrides for the backup schedule. Each frequency (`hourly`/`daily`/`weekly`/`monthly`/`yearly`) is
    optional. When provided, `retention_value` is required; `frequency_interval`/`retention_unit` fall back to
    the Atlas UI default for that frequency if omitted. When omitted:

    - If `skip_default_retentions=false` (the default), Atlas uses the following UI defaults for that frequency:
      - `hourly`: `frequency_interval=6`, `retention_unit="days"`, `retention_value=7`
      - `daily`: `retention_unit="days"`, `retention_value=7`
      - `weekly`: `frequency_interval=6`, `retention_unit="weeks"`, `retention_value=4`
      - `monthly`: `frequency_interval=40`, `retention_unit="months"`, `retention_value=12`
      - `yearly`: `frequency_interval=12`, `retention_unit="years"`, `retention_value=1`
    - If `skip_default_retentions=true`, the frequency is not created at all.

    `reference_hour_of_day`/`reference_minute_of_hour` control the UTC snapshot window (default: 18:00 UTC per
    Atlas's default backup policy when left unset). `restore_window_days` controls the PIT restore window.

    Each frequency block also accepts `copy_retention_value` (a number of days), the retention of the copy policy
    item the module derives for that frequency when `backup_copy_region` is set:

    - unset (`null`, the default): copy at the source frequency's retention.
    - `0`: do not create a copy policy item for the frequency.
    - positive: copy with that many days of retention, which must not exceed the source frequency's retention.

    It is mutually exclusive with `backup_copy_region.last_number_of_snapshots`. See the
    [Backup Guide](./docs/backup_guide.md#cross-region-copy) for the copy retention and count-based copy details.

    `ondemand` is accepted for shape-compatibility with the project module's future `backup_compliance_policy.retention`
    but has no corresponding field on `cloud_backup_schedule`. It is ignored by this module.

    Frequency fields (`hourly`/`daily`/`weekly`/`monthly`/`yearly`) are rejected (validation error) when
    `backup_mode = "ON_DEMAND"`; `restore_window_days` and `ondemand` remain valid there. The whole variable is
    rejected when `backup_mode = "UNMANAGED"` or `backup_enabled = false`.

    Atlas requires an `hourly` policy item for Continuous Cloud Backup: when `backup_mode = "SCHEDULED"` and
    point-in-time restore is effectively enabled (`pit_enabled` defaults to `backup_enabled`), omitting `hourly`
    via `skip_default_retentions = true` is rejected (validation error) rather than failing at apply.
  EOT
  type = object({
    skip_default_retentions  = optional(bool, false)
    restore_window_days      = optional(number)
    reference_hour_of_day    = optional(number)
    reference_minute_of_hour = optional(number)
    ondemand = optional(object({
      retention_unit  = optional(string, "days")
      retention_value = number
    }))
    hourly = optional(object({
      frequency_interval   = optional(number)
      retention_unit       = optional(string, "days")
      retention_value      = number
      copy_retention_value = optional(number)
    }))
    daily = optional(object({
      retention_unit       = optional(string, "days")
      retention_value      = number
      copy_retention_value = optional(number)
    }))
    weekly = optional(object({
      frequency_interval   = optional(number)
      retention_unit       = optional(string, "weeks")
      retention_value      = number
      copy_retention_value = optional(number)
    }))
    monthly = optional(object({
      frequency_interval   = optional(number)
      retention_unit       = optional(string, "months")
      retention_value      = number
      copy_retention_value = optional(number)
    }))
    yearly = optional(object({
      frequency_interval   = optional(number)
      retention_unit       = optional(string, "years")
      retention_value      = number
      copy_retention_value = optional(number)
    }))
  })
  nullable = true
  default  = null

  validation {
    condition     = var.backup_retention == null || (var.backup_mode != "UNMANAGED" && var.backup_enabled)
    error_message = "Cannot set backup_retention when backup_mode = \"UNMANAGED\" or backup_enabled = false."
  }

  validation {
    # try() per field -- a leading null-guard doesn't short-circuit here, see tests/plan_short_circuit.tftest.hcl.
    condition = var.backup_mode != "ON_DEMAND" || alltrue([
      try(var.backup_retention.hourly, null) == null,
      try(var.backup_retention.daily, null) == null,
      try(var.backup_retention.weekly, null) == null,
      try(var.backup_retention.monthly, null) == null,
      try(var.backup_retention.yearly, null) == null,
    ])
    error_message = "Cannot set frequency-based backup_retention fields (hourly/daily/weekly/monthly/yearly) when backup_mode = \"ON_DEMAND\" (it removes all frequency policies). restore_window_days and ondemand remain valid."
  }

  validation {
    # try() per field -- a leading null-guard doesn't short-circuit here, see tests/plan_short_circuit.tftest.hcl.
    condition = var.backup_mode != "SCHEDULED" || coalesce(var.pit_enabled, var.backup_enabled) != true || !(
      try(var.backup_retention.skip_default_retentions, false) && try(var.backup_retention.hourly, null) == null
    )
    error_message = "Cannot omit backup_retention.hourly (skip_default_retentions = true with hourly unset) when backup_mode = \"SCHEDULED\" and point-in-time restore is effectively enabled (pit_enabled defaults to backup_enabled) -- Atlas requires an hourly policy item for Continuous Cloud Backup."
  }
}

variable "backup_export" {
  description = <<-EOT
    Export snapshots to a cloud storage bucket. The bucket resource is managed by the CSP module
    (aws/azure/gcp backup_export submodules). Setting this hardcodes `auto_export_enabled = true` on the
    schedule; there is no independent toggle.

    Valid with `backup_mode = "ON_DEMAND"` (exports whatever snapshots exist). Rejected (validation error) when
    set together with `backup_mode = "UNMANAGED"` or `backup_enabled = false`.
  EOT
  type = object({
    export_bucket_id = string
    frequency_type   = string
  })
  nullable = true
  default  = null

  validation {
    # Same short-circuit caveat as backup_retention's validation above.
    condition     = try(contains(["daily", "weekly", "monthly", "yearly"], var.backup_export.frequency_type), true)
    error_message = "backup_export.frequency_type must be one of: daily, weekly, monthly, yearly."
  }

  validation {
    condition     = var.backup_export == null || (var.backup_mode != "UNMANAGED" && var.backup_enabled)
    error_message = "Cannot set backup_export when backup_mode = \"UNMANAGED\" or backup_enabled = false."
  }
}
