resource "mongodbatlas_project" "this" {
  is_collect_database_specifics_statistics_enabled = var.is_collect_database_specifics_statistics_enabled
  is_data_explorer_enabled                         = var.is_data_explorer_enabled
  is_extended_storage_sizes_enabled                = var.is_extended_storage_sizes_enabled
  is_performance_advisor_enabled                   = var.is_performance_advisor_enabled
  is_realtime_performance_panel_enabled            = var.is_realtime_performance_panel_enabled
  is_schema_advisor_enabled                        = var.is_schema_advisor_enabled
  is_slow_operation_thresholding_enabled           = var.is_slow_operation_thresholding_enabled
  name                                             = var.name
  org_id                                           = var.org_id
  project_owner_id                                 = var.project_owner_id
  region_usage_restrictions                        = var.region_usage_restrictions
  tags                                             = var.tags
  with_default_alerts_settings                     = var.with_default_alerts_settings

  dynamic "limits" {
    for_each = var.limits == null ? [] : var.limits
    content {
      name  = limits.value.name
      value = limits.value.value
    }
  }

  dynamic "teams" {
    for_each = var.teams == null ? [] : var.teams
    content {
      role_names = teams.value.role_names
      team_id    = teams.value.team_id
    }
  }
}