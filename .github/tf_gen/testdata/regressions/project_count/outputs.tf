output "cluster_count" {
  value = mongodbatlas_project.this[0].cluster_count
}

output "created" {
  value = mongodbatlas_project.this[0].created
}

output "id" {
  value = mongodbatlas_project.this[0].id
}

output "ip_addresses" {
  value       = mongodbatlas_project.this[0].ip_addresses
  description = "DEPRECATED"
}

output "ip_addresses_services" {
  value = mongodbatlas_project.this[0].ip_addresses == null ? null : mongodbatlas_project.this[0].ip_addresses.services
}

output "is_collect_database_specifics_statistics_enabled" {
  value = mongodbatlas_project.this[0].is_collect_database_specifics_statistics_enabled
}

output "is_data_explorer_enabled" {
  value = mongodbatlas_project.this[0].is_data_explorer_enabled
}

output "is_extended_storage_sizes_enabled" {
  value = mongodbatlas_project.this[0].is_extended_storage_sizes_enabled
}

output "is_performance_advisor_enabled" {
  value = mongodbatlas_project.this[0].is_performance_advisor_enabled
}

output "is_realtime_performance_panel_enabled" {
  value = mongodbatlas_project.this[0].is_realtime_performance_panel_enabled
}

output "is_schema_advisor_enabled" {
  value = mongodbatlas_project.this[0].is_schema_advisor_enabled
}

output "is_slow_operation_thresholding_enabled" {
  value       = mongodbatlas_project.this[0].is_slow_operation_thresholding_enabled
  description = "DEPRECATED"
}

output "limits_current_usage" {
  value = mongodbatlas_project.this[0].limits == null ? null : mongodbatlas_project.this[0].limits[*].current_usage
}

output "limits_default_limit" {
  value = mongodbatlas_project.this[0].limits == null ? null : mongodbatlas_project.this[0].limits[*].default_limit
}

output "limits_maximum_limit" {
  value = mongodbatlas_project.this[0].limits == null ? null : mongodbatlas_project.this[0].limits[*].maximum_limit
}

output "region_usage_restrictions" {
  value = mongodbatlas_project.this[0].region_usage_restrictions
}

output "with_default_alerts_settings" {
  value = mongodbatlas_project.this[0].with_default_alerts_settings
}