output "schedule" {
  description = "Internal-only: exposes the managed schedule resource so terraform test can assert on its attributes. This submodule is not invoked directly by consumers, and the root cluster module does not re-export this output. The projected object omits the provider-deprecated `copy_settings[*].frequencies`; add an attribute here before asserting on it from a test."
  value = {
    project_id                = mongodbatlas_cloud_backup_schedule.this.project_id
    cluster_name              = mongodbatlas_cloud_backup_schedule.this.cluster_name
    skip_destroy              = mongodbatlas_cloud_backup_schedule.this.skip_destroy
    reference_hour_of_day     = mongodbatlas_cloud_backup_schedule.this.reference_hour_of_day
    reference_minute_of_hour  = mongodbatlas_cloud_backup_schedule.this.reference_minute_of_hour
    restore_window_days       = mongodbatlas_cloud_backup_schedule.this.restore_window_days
    auto_export_enabled       = mongodbatlas_cloud_backup_schedule.this.auto_export_enabled
    copy_policy_items_enabled = mongodbatlas_cloud_backup_schedule.this.copy_policy_items_enabled
    update_copy_snapshots     = mongodbatlas_cloud_backup_schedule.this.update_copy_snapshots
    delete_copy_snapshots     = mongodbatlas_cloud_backup_schedule.this.delete_copy_snapshots
    policy_item_hourly        = mongodbatlas_cloud_backup_schedule.this.policy_item_hourly
    policy_item_daily         = mongodbatlas_cloud_backup_schedule.this.policy_item_daily
    policy_item_weekly        = mongodbatlas_cloud_backup_schedule.this.policy_item_weekly
    policy_item_monthly       = mongodbatlas_cloud_backup_schedule.this.policy_item_monthly
    policy_item_yearly        = mongodbatlas_cloud_backup_schedule.this.policy_item_yearly
    export                    = mongodbatlas_cloud_backup_schedule.this.export
    copy_settings = [
      for cs in mongodbatlas_cloud_backup_schedule.this.copy_settings : {
        cloud_provider           = cs.cloud_provider
        region_name              = cs.region_name
        zone_id                  = cs.zone_id
        should_copy_oplogs       = cs.should_copy_oplogs
        last_number_of_snapshots = cs.last_number_of_snapshots
        copy_policy_items        = cs.copy_policy_items
      }
    ]
  }
}
