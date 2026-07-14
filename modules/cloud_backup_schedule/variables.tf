variable "project_id" {
  description = "Unique 24-hexadecimal digit string that identifies your project."
  type        = string
}

variable "cluster_name" {
  description = "Name of the cluster the backup schedule applies to."
  type        = string
}

variable "backup_mode" {
  description = "Schedule mode: ON_DEMAND (all frequency-based policy items removed) or SCHEDULED (module-managed policy items). UNMANAGED is handled by the caller not invoking this module at all."
  type        = string

  validation {
    condition     = contains(["ON_DEMAND", "SCHEDULED"], var.backup_mode)
    error_message = "backup_mode must be one of: ON_DEMAND, SCHEDULED."
  }
}

variable "retention" {
  description = <<-EOT
    Retention configuration for the backup schedule. Each frequency (hourly/daily/weekly/monthly/yearly) is
    optional -- when omitted and skip_default_retentions=false (the default), the frequency is created with
    the Atlas UI default. When provided, retention_value is required; frequency_interval/retention_unit fall
    back to the Atlas UI default for that frequency if omitted. When skip_default_retentions=true, an omitted
    frequency is not created at all.

    `ondemand` is accepted for shape-compatibility with the project module's future `backup_compliance_policy.retention`
    but has no corresponding field on `cloud_backup_schedule` -- it is ignored by this submodule.
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
  description = "Fully-resolved cross-region copy target (region/cloud_provider/should_copy_oplogs already derived by the root module). Null disables copy_settings. cloud_provider is left null to let the provider infer it when the root module cannot resolve it."
  type = object({
    cloud_provider     = optional(string)
    region_name        = string
    should_copy_oplogs = bool
  })
  nullable = true
  default  = null
}

variable "export" {
  description = "Auto-export configuration. Null disables export."
  type = object({
    export_bucket_id = string
    frequency_type   = string
  })
  nullable = true
  default  = null
}

variable "skip_destroy" {
  description = "Maps to the provider's skip_destroy. When true, removes the schedule from Terraform state on destroy without deleting it in Atlas."
  type        = bool
  default     = false
}
