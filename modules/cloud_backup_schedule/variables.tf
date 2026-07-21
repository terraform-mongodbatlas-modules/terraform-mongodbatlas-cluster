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
    The schedule mode. Can be:
    - `ON_DEMAND`: all frequency-based policy items removed
    - `SCHEDULED`: uses module-managed policy items
    - `UNMANAGED`: handled by the caller not invoking this module at all
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

    `ondemand` is accepted for shape-compatibility with the project module's future `backup_compliance_policy.retention`
    but has no corresponding field on `cloud_backup_schedule`. It is ignored by this submodule.
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
  description = "Fully-resolved cross-region copy target. The root module already derives `region`,`cloud_provider`, and `should_copy_oplogs`. `null` disables `copy_settings`. `cloud_provider` is left `null` to let the provider infer it when the root module cannot resolve it."
  type = object({
    cloud_provider     = optional(string)
    region_name        = string
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
