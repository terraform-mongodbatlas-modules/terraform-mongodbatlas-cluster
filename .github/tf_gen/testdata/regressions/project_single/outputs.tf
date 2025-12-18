output "project" {
  value = {
    cluster_count = mongodbatlas_project.this.cluster_count
    created = mongodbatlas_project.this.created
    id = mongodbatlas_project.this.id
    ip_addresses = mongodbatlas_project.this.ip_addresses
    is_collect_database_specifics_statistics_enabled = mongodbatlas_project.this.is_collect_database_specifics_statistics_enabled
    is_data_explorer_enabled = mongodbatlas_project.this.is_data_explorer_enabled
    is_extended_storage_sizes_enabled = mongodbatlas_project.this.is_extended_storage_sizes_enabled
    is_performance_advisor_enabled = mongodbatlas_project.this.is_performance_advisor_enabled
    is_realtime_performance_panel_enabled = mongodbatlas_project.this.is_realtime_performance_panel_enabled
    is_schema_advisor_enabled = mongodbatlas_project.this.is_schema_advisor_enabled
    is_slow_operation_thresholding_enabled = mongodbatlas_project.this.is_slow_operation_thresholding_enabled
    limits = mongodbatlas_project.this.limits
    region_usage_restrictions = mongodbatlas_project.this.region_usage_restrictions
    with_default_alerts_settings = mongodbatlas_project.this.with_default_alerts_settings
  }
}