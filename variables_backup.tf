variable "backup_mode" {
  # TODO(CLOUDP-425282): link to the backup guide once published for the full deletion-workflow writeup.
  description = <<-EOT
    Schedule mode for backup. Controls whether and how the module manages the cloud_backup_schedule resource.
    backup_enabled is a separate cluster-level flag; backup_mode is ignored when backup_enabled = false.
    - ON_DEMAND: schedule resource created but all frequency policies removed (PIT + manual snapshots only)
    - SCHEDULED: module-managed frequency policies (hourly/daily/weekly/monthly/yearly)
    - UNMANAGED: module does not create the schedule resource. Consumer manages cloud_backup_schedule
      externally using a standalone resource. backup_copy_region, backup_retention, and backup_export must
      be left at their defaults; backup_schedule_skip_destroy is still allowed.

    Migrating to UNMANAGED with backup_schedule_skip_destroy = true requires two applies: set it to true
    first while backup_mode is still SCHEDULED/ON_DEMAND, then switch to UNMANAGED in a second apply.
    Setting both in the same apply does not skip the delete.
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
    Cross-region snapshot copy settings (multi-region snapshot distribution). When set, the module creates
    `copy_settings` to replicate scheduled and on-demand snapshots to the target region.
    - `region`: Atlas region name. When omitted (`backup_copy_region = {}`), the module auto-derives a secondary
      region from `var.regions` (the highest-priority region after the primary), so the copy target stays
      valid across regional failovers without a config change. Requires at least 2 regions in `var.regions`;
      fails validation otherwise. Not derived from `var.replication_specs` -- set region explicitly when using
      that variable. `GEOSHARDED` clusters get one cluster-wide copy target derived from the first zone's
      regions; per-zone copy targets are not supported.
    - `cloud_provider`: override for multi-cloud clusters (default: derived from the target region, or left
      for the provider to infer if it can't be resolved)
    - `should_copy_oplogs`: copy oplogs for point-in-time restore from the copy region (default: `true` if PIT enabled)
  EOT
  type = object({
    region             = optional(string)
    cloud_provider     = optional(string)
    should_copy_oplogs = optional(bool)
  })
  nullable = true
  default  = null

  validation {
    condition     = var.backup_copy_region == null || (var.backup_mode != "UNMANAGED" && var.backup_enabled)
    error_message = "Cannot set backup_copy_region when backup_mode = \"UNMANAGED\" or backup_enabled = false."
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
    optional. When `skip_default_retentions=false` (the default), an omitted frequency is created using the
    Atlas UI default; when provided, `retention_value` is required and `frequency_interval`/`retention_unit` fall
    back to the Atlas UI default for that frequency if omitted. Set `skip_default_retentions=true` to only
    create the frequencies you explicitly declare.

    `reference_hour_of_day`/`reference_minute_of_hour` control the UTC snapshot window (default: cluster creation
    time). `restore_window_days` controls the PIT restore window.

    `ondemand` is accepted for shape-compatibility with the project module's future `backup_compliance_policy.retention`
    but has no corresponding field on `cloud_backup_schedule`. It is ignored by this module.

    Frequency fields (`hourly`/`daily`/`weekly`/`monthly`/`yearly`) are rejected (validation error) when
    `backup_mode = "ON_DEMAND"`; `restore_window_days` and `ondemand` remain valid there. The whole variable is
    rejected when `backup_mode = "UNMANAGED"` or `backup_enabled = false`.
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
      frequency_interval = optional(number)
      retention_unit     = optional(string, "days")
      retention_value    = number
    }))
    daily = optional(object({
      retention_unit  = optional(string, "days")
      retention_value = number
    }))
    weekly = optional(object({
      frequency_interval = optional(number)
      retention_unit     = optional(string, "weeks")
      retention_value    = number
    }))
    monthly = optional(object({
      frequency_interval = optional(number)
      retention_unit     = optional(string, "months")
      retention_value    = number
    }))
    yearly = optional(object({
      frequency_interval = optional(number)
      retention_unit     = optional(string, "years")
      retention_value    = number
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
