
locals {
  validation_errors = compact(concat(
    [for r in var.cloud_backup_schedule.copy_settings : var.default_replication_spec_zone_id && r.zone_id == null ? "zone_id is required if no default_replication_spec_zone_id is provided" : ""],
    [for r in var.cloud_backup_schedule.copy_settings : var.default_replication_spec_provider_name && r.cloud_provider == null ? "cloud_provider is required if no default_replication_spec_provider_name is provided" : ""],
  ))
}

resource "mongodbatlas_cloud_backup_schedule" "this" {
  lifecycle {
    precondition {
      condition     = length(local.validation_errors) == 0
      error_message = join("\n", local.validation_errors)
    }
  }

  cluster_name = var.cluster_name
  project_id   = var.project_id

  auto_export_enabled = var.cloud_backup_schedule.auto_export_enabled
  dynamic "copy_settings" {
    for_each = var.cloud_backup_schedule.copy_settings
    content {
      region_name    = copy_settings.value.region_name
      cloud_provider = coalesce(copy_settings.value.cloud_provider, var.default_replication_spec_provider_name)
      zone_id        = coalesce(copy_settings.value.zone_id, var.default_replication_spec_zone_id)

      frequencies        = copy_settings.value.frequencies
      should_copy_oplogs = copy_settings.value.should_copy_oplogs
    }
  }
  dynamic "export" {
    for_each = var.cloud_backup_schedule.export == null ? [] : var.cloud_backup_schedule.export
    content {
      export_bucket_id = export.value.export_bucket_id
      frequency_type   = export.value.frequency_type
    }
  }
  dynamic "policy_item_daily" {
    for_each = var.cloud_backup_schedule.policy_item_daily == null ? [] : var.cloud_backup_schedule.policy_item_daily
    content {
      frequency_interval = policy_item_daily.value.frequency_interval
      retention_unit     = policy_item_daily.value.retention_unit
      retention_value    = policy_item_daily.value.retention_value
    }
  }
  dynamic "policy_item_hourly" {
    for_each = var.cloud_backup_schedule.policy_item_hourly == null ? [] : var.cloud_backup_schedule.policy_item_hourly
    content {
      frequency_interval = policy_item_hourly.value.frequency_interval
      retention_unit     = policy_item_hourly.value.retention_unit
      retention_value    = policy_item_hourly.value.retention_value
    }
  }
  dynamic "policy_item_monthly" {
    for_each = var.cloud_backup_schedule.policy_item_monthly == null ? [] : var.cloud_backup_schedule.policy_item_monthly
    content {
      frequency_interval = policy_item_monthly.value.frequency_interval
      retention_unit     = policy_item_monthly.value.retention_unit
      retention_value    = policy_item_monthly.value.retention_value
    }
  }
  dynamic "policy_item_weekly" {
    for_each = var.cloud_backup_schedule.policy_item_weekly == null ? [] : var.cloud_backup_schedule.policy_item_weekly
    content {
      frequency_interval = policy_item_weekly.value.frequency_interval
      retention_unit     = policy_item_weekly.value.retention_unit
      retention_value    = policy_item_weekly.value.retention_value
    }
  }
  dynamic "policy_item_yearly" {
    for_each = var.cloud_backup_schedule.policy_item_yearly == null ? [] : var.cloud_backup_schedule.policy_item_yearly
    content {
      frequency_interval = policy_item_yearly.value.frequency_interval
      retention_unit     = policy_item_yearly.value.retention_unit
      retention_value    = policy_item_yearly.value.retention_value
    }
  }
  reference_hour_of_day                    = var.cloud_backup_schedule.reference_hour_of_day
  reference_minute_of_hour                 = var.cloud_backup_schedule.reference_minute_of_hour
  restore_window_days                      = var.cloud_backup_schedule.restore_window_days
  update_snapshots                         = var.cloud_backup_schedule.update_snapshots
  use_org_and_group_names_in_export_prefix = var.cloud_backup_schedule.use_org_and_group_names_in_export_prefix
}
