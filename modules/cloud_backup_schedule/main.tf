locals {
  is_scheduled = var.backup_mode == "SCHEDULED"

  hourly_active  = local.is_scheduled && (var.retention.hourly != null || !var.retention.skip_default_retentions)
  daily_active   = local.is_scheduled && (var.retention.daily != null || !var.retention.skip_default_retentions)
  weekly_active  = local.is_scheduled && (var.retention.weekly != null || !var.retention.skip_default_retentions)
  monthly_active = local.is_scheduled && (var.retention.monthly != null || !var.retention.skip_default_retentions)
  yearly_active  = local.is_scheduled && (var.retention.yearly != null || !var.retention.skip_default_retentions)

  # Atlas UI defaults: https://www.mongodb.com/docs/atlas/architecture/current/backups/
  effective_hourly = local.hourly_active ? {
    frequency_interval = coalesce(try(var.retention.hourly.frequency_interval, null), 6)
    retention_unit     = coalesce(try(var.retention.hourly.retention_unit, null), "days")
    retention_value    = coalesce(try(var.retention.hourly.retention_value, null), 7)
  } : null

  effective_daily = local.daily_active ? {
    retention_unit  = coalesce(try(var.retention.daily.retention_unit, null), "days")
    retention_value = coalesce(try(var.retention.daily.retention_value, null), 7)
  } : null

  effective_weekly = local.weekly_active ? {
    frequency_interval = coalesce(try(var.retention.weekly.frequency_interval, null), 6)
    retention_unit     = coalesce(try(var.retention.weekly.retention_unit, null), "weeks")
    retention_value    = coalesce(try(var.retention.weekly.retention_value, null), 4)
  } : null

  effective_monthly = local.monthly_active ? {
    frequency_interval = coalesce(try(var.retention.monthly.frequency_interval, null), 40)
    retention_unit     = coalesce(try(var.retention.monthly.retention_unit, null), "months")
    retention_value    = coalesce(try(var.retention.monthly.retention_value, null), 12)
  } : null

  effective_yearly = local.yearly_active ? {
    frequency_interval = coalesce(try(var.retention.yearly.frequency_interval, null), 12)
    retention_unit     = coalesce(try(var.retention.yearly.retention_unit, null), "years")
    retention_value    = coalesce(try(var.retention.yearly.retention_value, null), 1)
  } : null

  # Copy every active frequency, plus ON_DEMAND (manual snapshots are always covered).
  copy_frequencies = concat(
    local.hourly_active ? ["HOURLY"] : [],
    local.daily_active ? ["DAILY"] : [],
    local.weekly_active ? ["WEEKLY"] : [],
    local.monthly_active ? ["MONTHLY"] : [],
    local.yearly_active ? ["YEARLY"] : [],
    ["ON_DEMAND"],
  )
}

resource "mongodbatlas_cloud_backup_schedule" "this" {
  project_id   = var.project_id
  cluster_name = var.cluster_name
  skip_destroy = var.skip_destroy

  reference_hour_of_day    = var.retention.reference_hour_of_day
  reference_minute_of_hour = var.retention.reference_minute_of_hour
  restore_window_days      = var.retention.restore_window_days

  auto_export_enabled = var.export != null

  dynamic "export" {
    for_each = var.export != null ? [var.export] : []
    content {
      export_bucket_id = export.value.export_bucket_id
      frequency_type   = export.value.frequency_type
    }
  }

  dynamic "copy_settings" {
    for_each = var.copy_settings != null ? [var.copy_settings] : []
    content {
      cloud_provider     = copy_settings.value.cloud_provider
      region_name        = copy_settings.value.region_name
      zone_id            = copy_settings.value.zone_id
      should_copy_oplogs = copy_settings.value.should_copy_oplogs
      frequencies        = local.copy_frequencies
    }
  }

  dynamic "policy_item_hourly" {
    for_each = local.effective_hourly != null ? [local.effective_hourly] : []
    content {
      frequency_interval = policy_item_hourly.value.frequency_interval
      retention_unit     = policy_item_hourly.value.retention_unit
      retention_value    = policy_item_hourly.value.retention_value
    }
  }

  dynamic "policy_item_daily" {
    for_each = local.effective_daily != null ? [local.effective_daily] : []
    content {
      frequency_interval = 1
      retention_unit     = policy_item_daily.value.retention_unit
      retention_value    = policy_item_daily.value.retention_value
    }
  }

  dynamic "policy_item_weekly" {
    for_each = local.effective_weekly != null ? [local.effective_weekly] : []
    content {
      frequency_interval = policy_item_weekly.value.frequency_interval
      retention_unit     = policy_item_weekly.value.retention_unit
      retention_value    = policy_item_weekly.value.retention_value
    }
  }

  dynamic "policy_item_monthly" {
    for_each = local.effective_monthly != null ? [local.effective_monthly] : []
    content {
      frequency_interval = policy_item_monthly.value.frequency_interval
      retention_unit     = policy_item_monthly.value.retention_unit
      retention_value    = policy_item_monthly.value.retention_value
    }
  }

  dynamic "policy_item_yearly" {
    for_each = local.effective_yearly != null ? [local.effective_yearly] : []
    content {
      frequency_interval = policy_item_yearly.value.frequency_interval
      retention_unit     = policy_item_yearly.value.retention_unit
      retention_value    = policy_item_yearly.value.retention_value
    }
  }
}
