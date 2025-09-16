variable "cluster_name" {
  type = string
}

variable "project_id" {
  type = string
}

variable "default_replication_spec_zone_id" {
  type    = string
  default = ""
}

variable "default_replication_spec_provider_name" {
  type    = string
  default = ""
}

variable "cloud_backup_schedule" {
  type = object({
    auto_export_enabled                      = optional(bool)
    reference_hour_of_day                    = optional(number)
    reference_minute_of_hour                 = optional(number)
    restore_window_days                      = optional(number)
    update_snapshots                         = optional(bool)
    use_org_and_group_names_in_export_prefix = optional(bool)
    copy_settings = optional(list(object({
      cloud_provider     = optional(string) # "AWS" | "GCP" | "AZURE"
      frequencies        = optional(list(string))
      region_name        = optional(string)
      should_copy_oplogs = optional(bool)
      zone_id            = optional(string)
    })))
    export = optional(list(object({
      export_bucket_id = optional(string)
      frequency_type   = optional(string)
    })))
    policy_item_daily = optional(list(object({
      frequency_interval = number
      retention_unit     = string
      retention_value    = number
    })))
    policy_item_hourly = optional(list(object({
      frequency_interval = number
      retention_unit     = string
      retention_value    = number
    })))
    policy_item_monthly = optional(list(object({
      frequency_interval = number
      retention_unit     = string
      retention_value    = number
    })))
    policy_item_weekly = optional(list(object({
      frequency_interval = number
      retention_unit     = string
      retention_value    = number
    })))
    policy_item_yearly = optional(list(object({
      frequency_interval = number
      retention_unit     = string
      retention_value    = number
    })))
  })
}
