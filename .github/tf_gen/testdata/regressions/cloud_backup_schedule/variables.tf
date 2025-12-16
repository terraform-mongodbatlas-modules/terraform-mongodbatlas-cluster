variable "cluster_name" {
  type = string
}

variable "project_id" {
  type = string
}

variable "auto_export_enabled" {
  type     = bool
  nullable = true
  default  = null
}

variable "copy_settings" {
  type = list(object({
    cloud_provider      = optional(string),
    frequencies         = optional(set(string)),
    region_name         = optional(string),
    replication_spec_id = optional(string),
    should_copy_oplogs  = optional(bool),
    zone_id             = optional(string)
  }))
  nullable = true
  default  = null
}

variable "export" {
  type = object({
    export_bucket_id = optional(string),
    frequency_type   = optional(string)
  })
  nullable = true
  default  = null
}

variable "policy_item_daily" {
  type = object({
    frequency_interval = number,
    retention_unit     = string,
    retention_value    = number
  })
  nullable = true
  default  = null
}

variable "policy_item_hourly" {
  type = object({
    frequency_interval = number,
    retention_unit     = string,
    retention_value    = number
  })
  nullable = true
  default  = null
}

variable "policy_item_monthly" {
  type = list(object({
    frequency_interval = number,
    retention_unit     = string,
    retention_value    = number
  }))
  nullable = true
  default  = null
}

variable "policy_item_weekly" {
  type = list(object({
    frequency_interval = number,
    retention_unit     = string,
    retention_value    = number
  }))
  nullable = true
  default  = null
}

variable "policy_item_yearly" {
  type = list(object({
    frequency_interval = number,
    retention_unit     = string,
    retention_value    = number
  }))
  nullable = true
  default  = null
}

variable "reference_hour_of_day" {
  type     = number
  nullable = true
  default  = null
}

variable "reference_minute_of_hour" {
  type     = number
  nullable = true
  default  = null
}

variable "restore_window_days" {
  type     = number
  nullable = true
  default  = null
}

variable "update_snapshots" {
  type     = bool
  nullable = true
  default  = null
}

variable "use_org_and_group_names_in_export_prefix" {
  type     = bool
  nullable = true
  default  = null
}