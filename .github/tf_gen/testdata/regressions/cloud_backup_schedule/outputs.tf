output "auto_export_enabled" {
  value = mongodbatlas_cloud_backup_schedule.this.auto_export_enabled
}

output "cluster_id" {
  value = mongodbatlas_cloud_backup_schedule.this.cluster_id
}

output "copy_settings_cloud_provider" {
  value = mongodbatlas_cloud_backup_schedule.this.copy_settings == null ? null : mongodbatlas_cloud_backup_schedule.this.copy_settings[*].cloud_provider
}

output "copy_settings_frequencies" {
  value = mongodbatlas_cloud_backup_schedule.this.copy_settings == null ? null : mongodbatlas_cloud_backup_schedule.this.copy_settings[*].frequencies
}

output "copy_settings_region_name" {
  value = mongodbatlas_cloud_backup_schedule.this.copy_settings == null ? null : mongodbatlas_cloud_backup_schedule.this.copy_settings[*].region_name
}

output "copy_settings_replication_spec_id" {
  value = mongodbatlas_cloud_backup_schedule.this.copy_settings == null ? null : mongodbatlas_cloud_backup_schedule.this.copy_settings[*].replication_spec_id
}

output "copy_settings_should_copy_oplogs" {
  value = mongodbatlas_cloud_backup_schedule.this.copy_settings == null ? null : mongodbatlas_cloud_backup_schedule.this.copy_settings[*].should_copy_oplogs
}

output "export_export_bucket_id" {
  value = mongodbatlas_cloud_backup_schedule.this.export == null ? null : mongodbatlas_cloud_backup_schedule.this.export[*].export_bucket_id
}

output "export_frequency_type" {
  value = mongodbatlas_cloud_backup_schedule.this.export == null ? null : mongodbatlas_cloud_backup_schedule.this.export[*].frequency_type
}

output "id" {
  value = mongodbatlas_cloud_backup_schedule.this.id
}

output "id_policy" {
  value = mongodbatlas_cloud_backup_schedule.this.id_policy
}

output "next_snapshot" {
  value = mongodbatlas_cloud_backup_schedule.this.next_snapshot
}

output "policy_item_daily_frequency_type" {
  value = mongodbatlas_cloud_backup_schedule.this.policy_item_daily == null ? null : mongodbatlas_cloud_backup_schedule.this.policy_item_daily[*].frequency_type
}

output "policy_item_daily_id" {
  value = mongodbatlas_cloud_backup_schedule.this.policy_item_daily == null ? null : mongodbatlas_cloud_backup_schedule.this.policy_item_daily[*].id
}

output "policy_item_hourly_frequency_type" {
  value = mongodbatlas_cloud_backup_schedule.this.policy_item_hourly == null ? null : mongodbatlas_cloud_backup_schedule.this.policy_item_hourly[*].frequency_type
}

output "policy_item_hourly_id" {
  value = mongodbatlas_cloud_backup_schedule.this.policy_item_hourly == null ? null : mongodbatlas_cloud_backup_schedule.this.policy_item_hourly[*].id
}

output "policy_item_monthly_frequency_type" {
  value = mongodbatlas_cloud_backup_schedule.this.policy_item_monthly == null ? null : mongodbatlas_cloud_backup_schedule.this.policy_item_monthly[*].frequency_type
}

output "policy_item_monthly_id" {
  value = mongodbatlas_cloud_backup_schedule.this.policy_item_monthly == null ? null : mongodbatlas_cloud_backup_schedule.this.policy_item_monthly[*].id
}

output "policy_item_weekly_frequency_type" {
  value = mongodbatlas_cloud_backup_schedule.this.policy_item_weekly == null ? null : mongodbatlas_cloud_backup_schedule.this.policy_item_weekly[*].frequency_type
}

output "policy_item_weekly_id" {
  value = mongodbatlas_cloud_backup_schedule.this.policy_item_weekly == null ? null : mongodbatlas_cloud_backup_schedule.this.policy_item_weekly[*].id
}

output "policy_item_yearly_frequency_type" {
  value = mongodbatlas_cloud_backup_schedule.this.policy_item_yearly == null ? null : mongodbatlas_cloud_backup_schedule.this.policy_item_yearly[*].frequency_type
}

output "policy_item_yearly_id" {
  value = mongodbatlas_cloud_backup_schedule.this.policy_item_yearly == null ? null : mongodbatlas_cloud_backup_schedule.this.policy_item_yearly[*].id
}

output "reference_hour_of_day" {
  value = mongodbatlas_cloud_backup_schedule.this.reference_hour_of_day
}

output "reference_minute_of_hour" {
  value = mongodbatlas_cloud_backup_schedule.this.reference_minute_of_hour
}

output "restore_window_days" {
  value = mongodbatlas_cloud_backup_schedule.this.restore_window_days
}

output "update_snapshots" {
  value = mongodbatlas_cloud_backup_schedule.this.update_snapshots
}

output "use_org_and_group_names_in_export_prefix" {
  value = mongodbatlas_cloud_backup_schedule.this.use_org_and_group_names_in_export_prefix
}