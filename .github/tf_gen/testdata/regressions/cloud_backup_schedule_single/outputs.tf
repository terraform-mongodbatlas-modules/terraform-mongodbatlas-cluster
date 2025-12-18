output "cloud_backup_schedule" {
  value = {
    cluster_id = mongodbatlas_cloud_backup_schedule.this.cluster_id
    copy_settings = mongodbatlas_cloud_backup_schedule.this.copy_settings
    export = mongodbatlas_cloud_backup_schedule.this.export
    id = mongodbatlas_cloud_backup_schedule.this.id
    id_policy = mongodbatlas_cloud_backup_schedule.this.id_policy
    next_snapshot = mongodbatlas_cloud_backup_schedule.this.next_snapshot
    policy_item_daily = mongodbatlas_cloud_backup_schedule.this.policy_item_daily
    policy_item_hourly = mongodbatlas_cloud_backup_schedule.this.policy_item_hourly
    policy_item_monthly = mongodbatlas_cloud_backup_schedule.this.policy_item_monthly
    policy_item_weekly = mongodbatlas_cloud_backup_schedule.this.policy_item_weekly
    policy_item_yearly = mongodbatlas_cloud_backup_schedule.this.policy_item_yearly
    reference_hour_of_day = mongodbatlas_cloud_backup_schedule.this.reference_hour_of_day
    reference_minute_of_hour = mongodbatlas_cloud_backup_schedule.this.reference_minute_of_hour
    restore_window_days = mongodbatlas_cloud_backup_schedule.this.restore_window_days
    update_snapshots = mongodbatlas_cloud_backup_schedule.this.update_snapshots
    use_org_and_group_names_in_export_prefix = mongodbatlas_cloud_backup_schedule.this.use_org_and_group_names_in_export_prefix
  }
}