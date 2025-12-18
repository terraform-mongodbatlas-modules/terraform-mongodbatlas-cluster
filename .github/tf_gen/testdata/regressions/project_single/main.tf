resource "mongodbatlas_project" "this" {
  is_collect_database_specifics_statistics_enabled = var.mongodbatlas_project.is_collect_database_specifics_statistics_enabled
  is_data_explorer_enabled                         = var.mongodbatlas_project.is_data_explorer_enabled
  is_extended_storage_sizes_enabled                = var.mongodbatlas_project.is_extended_storage_sizes_enabled
  is_performance_advisor_enabled                   = var.mongodbatlas_project.is_performance_advisor_enabled
  is_realtime_performance_panel_enabled            = var.mongodbatlas_project.is_realtime_performance_panel_enabled
  is_schema_advisor_enabled                        = var.mongodbatlas_project.is_schema_advisor_enabled
  is_slow_operation_thresholding_enabled           = var.mongodbatlas_project.is_slow_operation_thresholding_enabled
  name                                             = var.mongodbatlas_project.name
  org_id                                           = var.mongodbatlas_project.org_id
  project_owner_id                                 = var.mongodbatlas_project.project_owner_id
  region_usage_restrictions                        = var.mongodbatlas_project.region_usage_restrictions
  tags                                             = var.mongodbatlas_project.tags
  with_default_alerts_settings                     = var.mongodbatlas_project.with_default_alerts_settings

  dynamic "limits" {
    for_each = var.mongodbatlas_project.limits == null ? [] : var.mongodbatlas_project.limits
    content {
      name  = limits.value.name
      value = limits.value.value
    }
  }

  dynamic "teams" {
    for_each = var.mongodbatlas_project.teams == null ? [] : var.mongodbatlas_project.teams
    content {
      role_names = teams.value.role_names
      team_id    = teams.value.team_id
    }
  }
}