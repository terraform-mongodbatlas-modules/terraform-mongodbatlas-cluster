variable "mongodbatlas_project" {
  type = object({
    name                                             = string,
    org_id                                           = string,
    is_collect_database_specifics_statistics_enabled = optional(bool),
    is_data_explorer_enabled                         = optional(bool),
    is_extended_storage_sizes_enabled                = optional(bool),
    is_performance_advisor_enabled                   = optional(bool),
    is_realtime_performance_panel_enabled            = optional(bool),
    is_schema_advisor_enabled                        = optional(bool),
    is_slow_operation_thresholding_enabled           = optional(bool),
    limits = optional(set(object({
      name  = string,
      value = number
    }))),
    project_owner_id          = optional(string),
    region_usage_restrictions = optional(string),
    tags                      = optional(map(string)),
    teams = optional(set(object({
      role_names = set(string),
      team_id    = string
    }))),
    with_default_alerts_settings = optional(bool)
  })
}