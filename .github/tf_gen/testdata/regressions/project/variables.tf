variable "name" {
  type = string
}

variable "org_id" {
  type = string
}

variable "is_collect_database_specifics_statistics_enabled" {
  type     = bool
  nullable = true
  default  = null
}

variable "is_data_explorer_enabled" {
  type     = bool
  nullable = true
  default  = null
}

variable "is_extended_storage_sizes_enabled" {
  type     = bool
  nullable = true
  default  = null
}

variable "is_performance_advisor_enabled" {
  type     = bool
  nullable = true
  default  = null
}

variable "is_realtime_performance_panel_enabled" {
  type     = bool
  nullable = true
  default  = null
}

variable "is_schema_advisor_enabled" {
  type     = bool
  nullable = true
  default  = null
}

variable "is_slow_operation_thresholding_enabled" {
  type        = bool
  description = "DEPRECATED"
  nullable    = true
  default     = null
}

variable "limits" {
  type = set(object({
    name  = string,
    value = number
  }))
  nullable = true
  default  = null
}

variable "project_owner_id" {
  type     = string
  nullable = true
  default  = null
}

variable "region_usage_restrictions" {
  type     = string
  nullable = true
  default  = null
}

variable "tags" {
  type     = map(string)
  nullable = true
  default  = null
}

variable "teams" {
  type = set(object({
    role_names = set(string),
    team_id    = string
  }))
  nullable = true
  default  = null
}

variable "with_default_alerts_settings" {
  type     = bool
  nullable = true
  default  = null
}