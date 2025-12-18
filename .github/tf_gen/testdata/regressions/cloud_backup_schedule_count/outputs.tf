output "cluster_id" {
  value = length(mongodbatlas_cloud_backup_schedule.this) > 0 ? mongodbatlas_cloud_backup_schedule.this[0].cluster_id : null
}

output "copy_settings_cloud_provider" {
  value = length(mongodbatlas_cloud_backup_schedule.this) > 0 && mongodbatlas_cloud_backup_schedule.this[0].copy_settings != null ? mongodbatlas_cloud_backup_schedule.this[0].copy_settings[*].cloud_provider : null
}

output "copy_settings_frequencies" {
  value = length(mongodbatlas_cloud_backup_schedule.this) > 0 && mongodbatlas_cloud_backup_schedule.this[0].copy_settings != null ? mongodbatlas_cloud_backup_schedule.this[0].copy_settings[*].frequencies : null
}

output "copy_settings_region_name" {
  value = length(mongodbatlas_cloud_backup_schedule.this) > 0 && mongodbatlas_cloud_backup_schedule.this[0].copy_settings != null ? mongodbatlas_cloud_backup_schedule.this[0].copy_settings[*].region_name : null
}

output "copy_settings_should_copy_oplogs" {
  value = length(mongodbatlas_cloud_backup_schedule.this) > 0 && mongodbatlas_cloud_backup_schedule.this[0].copy_settings != null ? mongodbatlas_cloud_backup_schedule.this[0].copy_settings[*].should_copy_oplogs : null
}

output "copy_settings_zone_id" {
  value = length(mongodbatlas_cloud_backup_schedule.this) > 0 && mongodbatlas_cloud_backup_schedule.this[0].copy_settings != null ? mongodbatlas_cloud_backup_schedule.this[0].copy_settings[*].zone_id : null
}

output "export_export_bucket_id" {
  value = length(mongodbatlas_cloud_backup_schedule.this) > 0 && mongodbatlas_cloud_backup_schedule.this[0].export != null ? mongodbatlas_cloud_backup_schedule.this[0].export[*].export_bucket_id : null
}

output "export_frequency_type" {
  value = length(mongodbatlas_cloud_backup_schedule.this) > 0 && mongodbatlas_cloud_backup_schedule.this[0].export != null ? mongodbatlas_cloud_backup_schedule.this[0].export[*].frequency_type : null
}

output "id" {
  value = length(mongodbatlas_cloud_backup_schedule.this) > 0 ? mongodbatlas_cloud_backup_schedule.this[0].id : null
}

output "id_policy" {
  value = length(mongodbatlas_cloud_backup_schedule.this) > 0 ? mongodbatlas_cloud_backup_schedule.this[0].id_policy : null
}

output "next_snapshot" {
  value = length(mongodbatlas_cloud_backup_schedule.this) > 0 ? mongodbatlas_cloud_backup_schedule.this[0].next_snapshot : null
}

output "policy_item_daily_frequency_type" {
  value = length(mongodbatlas_cloud_backup_schedule.this) > 0 && mongodbatlas_cloud_backup_schedule.this[0].policy_item_daily != null ? mongodbatlas_cloud_backup_schedule.this[0].policy_item_daily[*].frequency_type : null
}

output "policy_item_daily_id" {
  value = length(mongodbatlas_cloud_backup_schedule.this) > 0 && mongodbatlas_cloud_backup_schedule.this[0].policy_item_daily != null ? mongodbatlas_cloud_backup_schedule.this[0].policy_item_daily[*].id : null
}

output "policy_item_hourly_frequency_type" {
  value = length(mongodbatlas_cloud_backup_schedule.this) > 0 && mongodbatlas_cloud_backup_schedule.this[0].policy_item_hourly != null ? mongodbatlas_cloud_backup_schedule.this[0].policy_item_hourly[*].frequency_type : null
}

output "policy_item_hourly_id" {
  value = length(mongodbatlas_cloud_backup_schedule.this) > 0 && mongodbatlas_cloud_backup_schedule.this[0].policy_item_hourly != null ? mongodbatlas_cloud_backup_schedule.this[0].policy_item_hourly[*].id : null
}

output "policy_item_monthly_frequency_type" {
  value = length(mongodbatlas_cloud_backup_schedule.this) > 0 && mongodbatlas_cloud_backup_schedule.this[0].policy_item_monthly != null ? mongodbatlas_cloud_backup_schedule.this[0].policy_item_monthly[*].frequency_type : null
}

output "policy_item_monthly_id" {
  value = length(mongodbatlas_cloud_backup_schedule.this) > 0 && mongodbatlas_cloud_backup_schedule.this[0].policy_item_monthly != null ? mongodbatlas_cloud_backup_schedule.this[0].policy_item_monthly[*].id : null
}

output "policy_item_weekly_frequency_type" {
  value = length(mongodbatlas_cloud_backup_schedule.this) > 0 && mongodbatlas_cloud_backup_schedule.this[0].policy_item_weekly != null ? mongodbatlas_cloud_backup_schedule.this[0].policy_item_weekly[*].frequency_type : null
}

output "policy_item_weekly_id" {
  value = length(mongodbatlas_cloud_backup_schedule.this) > 0 && mongodbatlas_cloud_backup_schedule.this[0].policy_item_weekly != null ? mongodbatlas_cloud_backup_schedule.this[0].policy_item_weekly[*].id : null
}

output "policy_item_yearly_frequency_type" {
  value = length(mongodbatlas_cloud_backup_schedule.this) > 0 && mongodbatlas_cloud_backup_schedule.this[0].policy_item_yearly != null ? mongodbatlas_cloud_backup_schedule.this[0].policy_item_yearly[*].frequency_type : null
}

output "policy_item_yearly_id" {
  value = length(mongodbatlas_cloud_backup_schedule.this) > 0 && mongodbatlas_cloud_backup_schedule.this[0].policy_item_yearly != null ? mongodbatlas_cloud_backup_schedule.this[0].policy_item_yearly[*].id : null
}

output "reference_hour_of_day" {
  value = length(mongodbatlas_cloud_backup_schedule.this) > 0 ? mongodbatlas_cloud_backup_schedule.this[0].reference_hour_of_day : null
}

output "reference_minute_of_hour" {
  value = length(mongodbatlas_cloud_backup_schedule.this) > 0 ? mongodbatlas_cloud_backup_schedule.this[0].reference_minute_of_hour : null
}

output "restore_window_days" {
  value = length(mongodbatlas_cloud_backup_schedule.this) > 0 ? mongodbatlas_cloud_backup_schedule.this[0].restore_window_days : null
}

output "update_snapshots" {
  value = length(mongodbatlas_cloud_backup_schedule.this) > 0 ? mongodbatlas_cloud_backup_schedule.this[0].update_snapshots : null
}

output "use_org_and_group_names_in_export_prefix" {
  value = length(mongodbatlas_cloud_backup_schedule.this) > 0 ? mongodbatlas_cloud_backup_schedule.this[0].use_org_and_group_names_in_export_prefix : null
}