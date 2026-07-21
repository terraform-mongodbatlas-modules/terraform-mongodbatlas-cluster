output "cluster_count" {
  value = length(mongodbatlas_project.this) > 0 ? mongodbatlas_project.this[0].cluster_count : null
}

output "created" {
  value = length(mongodbatlas_project.this) > 0 ? mongodbatlas_project.this[0].created : null
}

output "ip_addresses" {
  value       = length(mongodbatlas_project.this) > 0 ? mongodbatlas_project.this[0].ip_addresses : null
  description = "DEPRECATED"
}

output "ip_addresses_services" {
  value = length(mongodbatlas_project.this) > 0 && mongodbatlas_project.this[0].ip_addresses != null ? mongodbatlas_project.this[0].ip_addresses.services : null
}

output "is_collect_database_specifics_statistics_enabled" {
  value = length(mongodbatlas_project.this) > 0 ? mongodbatlas_project.this[0].is_collect_database_specifics_statistics_enabled : null
}

output "is_data_explorer_enabled" {
  value = length(mongodbatlas_project.this) > 0 ? mongodbatlas_project.this[0].is_data_explorer_enabled : null
}

output "is_extended_storage_sizes_enabled" {
  value = length(mongodbatlas_project.this) > 0 ? mongodbatlas_project.this[0].is_extended_storage_sizes_enabled : null
}

output "is_performance_advisor_enabled" {
  value = length(mongodbatlas_project.this) > 0 ? mongodbatlas_project.this[0].is_performance_advisor_enabled : null
}

output "is_realtime_performance_panel_enabled" {
  value = length(mongodbatlas_project.this) > 0 ? mongodbatlas_project.this[0].is_realtime_performance_panel_enabled : null
}

output "is_schema_advisor_enabled" {
  value = length(mongodbatlas_project.this) > 0 ? mongodbatlas_project.this[0].is_schema_advisor_enabled : null
}

output "is_slow_operation_thresholding_enabled" {
  value       = length(mongodbatlas_project.this) > 0 ? mongodbatlas_project.this[0].is_slow_operation_thresholding_enabled : null
  description = "DEPRECATED"
}

output "limits_current_usage" {
  value = length(mongodbatlas_project.this) > 0 && mongodbatlas_project.this[0].limits != null ? mongodbatlas_project.this[0].limits[*].current_usage : null
}

output "limits_default_limit" {
  value = length(mongodbatlas_project.this) > 0 && mongodbatlas_project.this[0].limits != null ? mongodbatlas_project.this[0].limits[*].default_limit : null
}

output "limits_maximum_limit" {
  value = length(mongodbatlas_project.this) > 0 && mongodbatlas_project.this[0].limits != null ? mongodbatlas_project.this[0].limits[*].maximum_limit : null
}

output "region_usage_restrictions" {
  value = length(mongodbatlas_project.this) > 0 ? mongodbatlas_project.this[0].region_usage_restrictions : null
}

output "with_default_alerts_settings" {
  value = length(mongodbatlas_project.this) > 0 ? mongodbatlas_project.this[0].with_default_alerts_settings : null
}