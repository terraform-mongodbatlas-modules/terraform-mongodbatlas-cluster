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

  # Copy policy items replace the deprecated legacy frequency list: one item per active frequency whose
  # `copy_retention_value` is not 0, plus a trailing ON_DEMAND item. `copy_retention_value` is a number of
  # days; unset copies at the source retention, and a positive value overrides it (Atlas rejects a value
  # greater than the source frequency's retention).
  copy_policy_item_hourly = local.hourly_active ? (
    try(var.retention.hourly.copy_retention_value, null) == 0 ? [] : [{
      frequency_type  = "hourly"
      retention_unit  = try(var.retention.hourly.copy_retention_value, null) == null ? local.effective_hourly.retention_unit : "days"
      retention_value = coalesce(try(var.retention.hourly.copy_retention_value, null), local.effective_hourly.retention_value)
    }]
  ) : []

  copy_policy_item_daily = local.daily_active ? (
    try(var.retention.daily.copy_retention_value, null) == 0 ? [] : [{
      frequency_type  = "daily"
      retention_unit  = try(var.retention.daily.copy_retention_value, null) == null ? local.effective_daily.retention_unit : "days"
      retention_value = coalesce(try(var.retention.daily.copy_retention_value, null), local.effective_daily.retention_value)
    }]
  ) : []

  copy_policy_item_weekly = local.weekly_active ? (
    try(var.retention.weekly.copy_retention_value, null) == 0 ? [] : [{
      frequency_type  = "weekly"
      retention_unit  = try(var.retention.weekly.copy_retention_value, null) == null ? local.effective_weekly.retention_unit : "days"
      retention_value = coalesce(try(var.retention.weekly.copy_retention_value, null), local.effective_weekly.retention_value)
    }]
  ) : []

  copy_policy_item_monthly = local.monthly_active ? (
    try(var.retention.monthly.copy_retention_value, null) == 0 ? [] : [{
      frequency_type  = "monthly"
      retention_unit  = try(var.retention.monthly.copy_retention_value, null) == null ? local.effective_monthly.retention_unit : "days"
      retention_value = coalesce(try(var.retention.monthly.copy_retention_value, null), local.effective_monthly.retention_value)
    }]
  ) : []

  copy_policy_item_yearly = local.yearly_active ? (
    try(var.retention.yearly.copy_retention_value, null) == 0 ? [] : [{
      frequency_type  = "yearly"
      retention_unit  = try(var.retention.yearly.copy_retention_value, null) == null ? local.effective_yearly.retention_unit : "days"
      retention_value = coalesce(try(var.retention.yearly.copy_retention_value, null), local.effective_yearly.retention_value)
    }]
  ) : []

  # ON_DEMAND has no retention of its own (copies inherit the source snapshot's retention).
  copy_policy_items = concat(
    local.copy_policy_item_hourly,
    local.copy_policy_item_daily,
    local.copy_policy_item_weekly,
    local.copy_policy_item_monthly,
    local.copy_policy_item_yearly,
    [{ frequency_type = "ondemand", retention_unit = null, retention_value = null }],
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

  # The provider requires this flag for both `copy_policy_items` and `last_number_of_snapshots`.
  copy_policy_items_enabled = length(var.copy_settings) > 0
  update_copy_snapshots     = var.update_copy_snapshots
  delete_copy_snapshots     = var.delete_copy_snapshots

  dynamic "export" {
    for_each = var.export != null ? [var.export] : []
    content {
      export_bucket_id = export.value.export_bucket_id
      frequency_type   = export.value.frequency_type
    }
  }

  dynamic "copy_settings" {
    for_each = var.copy_settings
    content {
      cloud_provider           = copy_settings.value.cloud_provider
      region_name              = copy_settings.value.region_name
      zone_id                  = copy_settings.value.zone_id
      should_copy_oplogs       = copy_settings.value.should_copy_oplogs
      last_number_of_snapshots = copy_settings.value.last_number_of_snapshots

      # Exactly one copy mechanism per entry: count-based copies or the derived copy policy items.
      dynamic "copy_policy_items" {
        for_each = copy_settings.value.last_number_of_snapshots == null ? local.copy_policy_items : []
        content {
          frequency_type  = copy_policy_items.value.frequency_type
          retention_unit  = copy_policy_items.value.retention_unit
          retention_value = copy_policy_items.value.retention_value
        }
      }
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
