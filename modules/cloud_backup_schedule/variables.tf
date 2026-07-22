variable "project_id" {
  description = "Unique 24-hexadecimal digit string that identifies your project."
  type        = string
}

variable "cluster_name" {
  description = "Name of the cluster the backup schedule applies to."
  type        = string
}

variable "backup_mode" {
  description = <<-EOT
    Schedule mode for backup. Controls whether and how this submodule manages the `cloud_backup_schedule` resource.
    - `ON_DEMAND`: schedule resource created but all frequency policies removed (PIT + manual snapshots only)
    - `SCHEDULED`: module-managed frequency policies (`hourly`/`daily`/`weekly`/`monthly`/`yearly`)
    - `UNMANAGED`: not a valid value here -- handled by the caller not invoking this submodule at all.
      `copy_settings`, `retention`, and `export` are then irrelevant; `skip_destroy` still matters to the caller's
      own standalone `cloud_backup_schedule` resource.

    Migrating to `UNMANAGED` with `skip_destroy = true` requires two applies: set it to `true` first while
    `backup_mode` is still `SCHEDULED`/`ON_DEMAND` (this submodule still invoked), then stop invoking this
    submodule (switch the caller to `UNMANAGED`) in a second apply. Setting both in the same apply does not
    skip the delete.
  EOT
  type        = string

  validation {
    condition     = contains(["ON_DEMAND", "SCHEDULED"], var.backup_mode)
    error_message = "backup_mode must be one of: ON_DEMAND, SCHEDULED."
  }
}

variable "retention" {
  description = <<-EOT
    Retention configuration for the backup schedule. Each frequency (`hourly`/`daily`/`weekly`/`monthly`/`yearly`)
    is optional. When a frequency block is provided, `retention_value` is required; `frequency_interval` and
    `retention_unit` fall back to the Atlas UI default for that frequency if omitted. When a frequency block is
    omitted:

    - If `skip_default_retentions=false` (the default), Atlas uses the following UI defaults for that frequency:
      - `hourly`: `frequency_interval=6`, `retention_unit="days"`, `retention_value=7`
      - `daily`: `retention_unit="days"`, `retention_value=7`
      - `weekly`: `frequency_interval=6`, `retention_unit="weeks"`, `retention_value=4`
      - `monthly`: `frequency_interval=40`, `retention_unit="months"`, `retention_value=12`
      - `yearly`: `frequency_interval=12`, `retention_unit="years"`, `retention_value=1`
    - If `skip_default_retentions=true`, the frequency is not created at all.

    `reference_hour_of_day`/`reference_minute_of_hour` control the UTC snapshot window (default: cluster creation
    time). `restore_window_days` controls the PIT restore window.

    `ondemand` is accepted for shape-compatibility with the project module's future `backup_compliance_policy.retention`
    but has no corresponding field on `cloud_backup_schedule`. It is ignored by this submodule.

    Frequency fields (`hourly`/`daily`/`weekly`/`monthly`/`yearly`) are silently ignored (not rejected) when
    `var.backup_mode = "ON_DEMAND"`, since this submodule has no `backup_enabled`/`pit_enabled` input to validate
    against -- the root module rejects them (validation error) instead.

    Atlas requires an `hourly` policy item for Continuous Cloud Backup: if the cluster this schedule applies to
    has point-in-time restore enabled and `var.backup_mode = "SCHEDULED"`, omitting `hourly` (via
    `skip_default_retentions = true`) is rejected by Atlas at apply. This submodule has no visibility into
    whether PIT is enabled on the cluster, so it cannot validate this itself -- the root module's
    `backup_retention` validation catches it at `terraform plan` instead.
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
  default = {}
}

variable "copy_settings" {
  description = "Fully-resolved cross-region copy target. The root module already derives `region`,`cloud_provider`, `zone_id`, and `should_copy_oplogs`. `null` disables `copy_settings`. `cloud_provider` is left `null` to let the provider infer it when the root module cannot resolve it. `zone_id` disambiguates the copy target's zone on multi-zone (`GEOSHARDED`) clusters and is left `null` only when the root module could not resolve it."
  type = object({
    cloud_provider     = optional(string)
    region_name        = string
    zone_id            = optional(string)
    should_copy_oplogs = bool
  })
  nullable = true
  default  = null
}

variable "export" {
  description = "Auto-export configuration. `null` disables export."
  type = object({
    export_bucket_id = string
    frequency_type   = string
  })
  nullable = true
  default  = null
}

variable "skip_destroy" {
  description = "Maps to the provider's `skip_destroy`. When `true`, removes the schedule from Terraform state on destroy without deleting it in Atlas."
  type        = bool
  default     = false
}
