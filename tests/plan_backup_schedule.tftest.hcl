mock_provider "mongodbatlas" {}

variables {
  project_id = "000000000000000000000000"
}

run "scheduled_default_creates_ui_default_policy_items" {
  command = plan
  module { source = "./" }

  variables {
    name          = "tf-test-backup-default"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "REPLICASET"
    regions       = [{ name = "US_EAST_1", node_count = 3 }]
  }

  assert {
    condition     = length(module.backup_schedule) == 1
    error_message = "backup_schedule submodule should be created when backup_enabled=true and backup_mode!=UNMANAGED"
  }

  assert {
    condition     = module.backup_schedule[0].schedule.policy_item_hourly[0].retention_value == 7
    error_message = "hourly retention should default to 7 days"
  }

  assert {
    condition     = module.backup_schedule[0].schedule.policy_item_daily[0].retention_value == 7
    error_message = "daily retention should default to 7 days"
  }

  assert {
    condition     = module.backup_schedule[0].schedule.policy_item_weekly[0].retention_value == 4
    error_message = "weekly retention should default to 4 weeks"
  }

  assert {
    condition     = module.backup_schedule[0].schedule.policy_item_monthly[0].retention_value == 12
    error_message = "monthly retention should default to 12 months"
  }

  assert {
    condition     = module.backup_schedule[0].schedule.policy_item_yearly[0].retention_value == 1
    error_message = "yearly retention should default to 1 year"
  }

  assert {
    condition     = module.backup_schedule[0].schedule.skip_destroy == false
    error_message = "skip_destroy should default to false (backup_schedule_deletion_policy=DELETE)"
  }
}

run "backup_disabled_skips_schedule" {
  command = plan
  module { source = "./" }

  variables {
    name           = "tf-test-backup-disabled"
    project_id     = var.project_id
    provider_name  = "AWS"
    cluster_type   = "REPLICASET"
    instance_size  = "M10"
    backup_enabled = false
    auto_scaling   = { compute_enabled = false }
    regions        = [{ name = "US_EAST_1", node_count = 3 }]
  }

  assert {
    condition     = length(module.backup_schedule) == 0
    error_message = "backup_schedule submodule should not be created when backup_enabled=false"
  }
}

run "unmanaged_mode_skips_schedule" {
  command = plan
  module { source = "./" }

  variables {
    name          = "tf-test-backup-unmanaged"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "REPLICASET"
    backup_mode   = "UNMANAGED"
    regions       = [{ name = "US_EAST_1", node_count = 3 }]
  }

  assert {
    condition     = length(module.backup_schedule) == 0
    error_message = "backup_schedule submodule should not be created when backup_mode=UNMANAGED"
  }
}

run "on_demand_mode_removes_frequency_policies" {
  command = plan
  module { source = "./" }

  variables {
    name          = "tf-test-backup-ondemand"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "REPLICASET"
    backup_mode   = "ON_DEMAND"
    regions       = [{ name = "US_EAST_1", node_count = 3 }]
  }

  assert {
    condition     = length(module.backup_schedule[0].schedule.policy_item_hourly) == 0
    error_message = "ON_DEMAND mode should not create any hourly policy item"
  }

  assert {
    condition     = length(module.backup_schedule[0].schedule.policy_item_daily) == 0
    error_message = "ON_DEMAND mode should not create any daily policy item"
  }
}

run "on_demand_mode_with_frequency_retention_fails" {
  command         = plan
  expect_failures = [var.backup_retention]
  module { source = "./" }

  variables {
    name          = "tf-test-backup-ondemand-conflict"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "REPLICASET"
    backup_mode   = "ON_DEMAND"
    regions       = [{ name = "US_EAST_1", node_count = 3 }]
    backup_retention = {
      daily = { retention_value = 14 }
    }
  }
}

run "on_demand_mode_with_copy_region_succeeds" {
  command = plan
  module { source = "./" }

  variables {
    name               = "tf-test-backup-ondemand-copy"
    project_id         = var.project_id
    provider_name      = "AWS"
    cluster_type       = "REPLICASET"
    backup_mode        = "ON_DEMAND"
    regions            = [{ name = "US_EAST_1", node_count = 3 }, { name = "US_WEST_2", node_count = 2 }]
    backup_copy_region = {}
  }

  assert {
    condition     = module.backup_schedule[0].schedule.copy_settings[0].region_name == "US_WEST_2"
    error_message = "ON_DEMAND mode should still allow cross-region copy of on-demand snapshots"
  }

  assert {
    condition     = length(module.backup_schedule[0].schedule.copy_settings[0].frequencies) == 1 && contains(module.backup_schedule[0].schedule.copy_settings[0].frequencies, "ON_DEMAND")
    error_message = "ON_DEMAND mode should only copy the ON_DEMAND frequency (no scheduled frequencies exist)"
  }
}

run "on_demand_mode_with_export_succeeds" {
  command = plan
  module { source = "./" }

  variables {
    name          = "tf-test-backup-ondemand-export"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "REPLICASET"
    backup_mode   = "ON_DEMAND"
    regions       = [{ name = "US_EAST_1", node_count = 3 }]
    backup_export = {
      export_bucket_id = "000000000000000000000000"
      frequency_type   = "monthly"
    }
  }

  assert {
    condition     = module.backup_schedule[0].schedule.auto_export_enabled == true
    error_message = "ON_DEMAND mode should still allow exporting whatever snapshots exist"
  }
}

run "unmanaged_mode_with_copy_region_fails" {
  command         = plan
  expect_failures = [var.backup_copy_region]
  module { source = "./" }

  variables {
    name               = "tf-test-backup-unmanaged-conflict"
    project_id         = var.project_id
    provider_name      = "AWS"
    cluster_type       = "REPLICASET"
    backup_mode        = "UNMANAGED"
    regions            = [{ name = "US_EAST_1", node_count = 3 }]
    backup_copy_region = {}
  }
}

run "backup_disabled_with_retention_fails" {
  command         = plan
  expect_failures = [var.backup_retention]
  module { source = "./" }

  variables {
    name           = "tf-test-backup-disabled-conflict"
    project_id     = var.project_id
    provider_name  = "AWS"
    cluster_type   = "REPLICASET"
    instance_size  = "M10"
    backup_enabled = false
    auto_scaling   = { compute_enabled = false }
    regions        = [{ name = "US_EAST_1", node_count = 3 }]
    backup_retention = {
      daily = { retention_value = 14 }
    }
  }
}

run "retention_override_merges_with_defaults" {
  command = plan
  module { source = "./" }

  variables {
    name          = "tf-test-backup-retention-override"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "REPLICASET"
    regions       = [{ name = "US_EAST_1", node_count = 3 }]
    backup_retention = {
      daily = { retention_value = 30 }
    }
  }

  assert {
    condition     = module.backup_schedule[0].schedule.policy_item_daily[0].retention_value == 30
    error_message = "daily retention_value override should be respected"
  }

  assert {
    condition     = module.backup_schedule[0].schedule.policy_item_daily[0].retention_unit == "days"
    error_message = "daily retention_unit should fall back to the Atlas UI default (days) when not overridden"
  }

  assert {
    condition     = module.backup_schedule[0].schedule.policy_item_hourly[0].retention_value == 7
    error_message = "hourly retention should remain at the default when only daily is overridden"
  }
}

run "skip_default_retentions_only_creates_declared_frequencies" {
  command = plan
  module { source = "./" }

  variables {
    name          = "tf-test-backup-skip-defaults"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "REPLICASET"
    regions       = [{ name = "US_EAST_1", node_count = 3 }]
    backup_retention = {
      skip_default_retentions = true
      daily                   = { retention_value = 30 }
    }
  }

  assert {
    condition     = length(module.backup_schedule[0].schedule.policy_item_daily) == 1
    error_message = "daily should be created since it was explicitly declared"
  }

  assert {
    condition     = length(module.backup_schedule[0].schedule.policy_item_hourly) == 0
    error_message = "hourly should not be created when skip_default_retentions=true and hourly was not declared"
  }
}

run "copy_region_auto_derives_secondary" {
  command = plan
  module { source = "./" }

  variables {
    name               = "tf-test-backup-copy-auto"
    project_id         = var.project_id
    provider_name      = "AWS"
    cluster_type       = "REPLICASET"
    regions            = [{ name = "US_EAST_1", node_count = 3 }, { name = "US_WEST_2", node_count = 2 }]
    backup_copy_region = {}
  }

  assert {
    condition     = module.backup_schedule[0].schedule.copy_settings[0].region_name == "US_WEST_2"
    error_message = "copy region should auto-derive to the second-priority region"
  }

  assert {
    condition     = module.backup_schedule[0].schedule.copy_settings[0].should_copy_oplogs == true
    error_message = "should_copy_oplogs should default to true when PIT is enabled"
  }
}

run "copy_region_should_copy_oplogs_defaults_false_when_pit_disabled" {
  command = plan
  module { source = "./" }

  variables {
    name               = "tf-test-backup-copy-no-pit"
    project_id         = var.project_id
    provider_name      = "AWS"
    cluster_type       = "REPLICASET"
    pit_enabled        = false
    regions            = [{ name = "US_EAST_1", node_count = 3 }, { name = "US_WEST_2", node_count = 2 }]
    backup_copy_region = {}
  }

  assert {
    condition     = module.backup_schedule[0].schedule.copy_settings[0].should_copy_oplogs == false
    error_message = "should_copy_oplogs should default to false when PIT is disabled"
  }
}

run "copy_region_pinned_explicit_region" {
  command = plan
  module { source = "./" }

  variables {
    name          = "tf-test-backup-copy-pinned"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "REPLICASET"
    regions       = [{ name = "US_EAST_1", node_count = 3 }, { name = "US_WEST_2", node_count = 2 }]
    backup_copy_region = {
      region = "EU_WEST_1"
    }
  }

  assert {
    condition     = module.backup_schedule[0].schedule.copy_settings[0].region_name == "EU_WEST_1"
    error_message = "explicit region should be respected over auto-derivation"
  }
}

run "copy_region_pinned_region_outside_topology_without_root_provider_name" {
  command = plan
  module { source = "./" }

  variables {
    name         = "tf-test-backup-copy-pinned-no-root-provider"
    project_id   = var.project_id
    cluster_type = "REPLICASET"
    regions      = [{ name = "US_EAST_1", node_count = 3, provider_name = "AWS" }]
    backup_copy_region = {
      region = "EU_WEST_1"
    }
  }

  # cloud_provider can't be asserted here: with no root provider_name and no match in var.regions, it's left
  # optional+computed (unknown until apply) -- that's correct behavior, not something a plan-only test can check.
  assert {
    condition     = module.backup_schedule[0].schedule.copy_settings[0].region_name == "EU_WEST_1"
    error_message = "explicit region outside the cluster topology should still be respected"
  }
}

run "copy_region_insufficient_regions_fails" {
  command         = plan
  expect_failures = [mongodbatlas_advanced_cluster.this]
  module { source = "./" }

  variables {
    name               = "tf-test-backup-copy-insufficient"
    project_id         = var.project_id
    provider_name      = "AWS"
    cluster_type       = "REPLICASET"
    regions            = [{ name = "US_EAST_1", node_count = 3 }]
    backup_copy_region = {}
  }
}

run "copy_region_replication_specs_requires_explicit_region" {
  command         = plan
  expect_failures = [mongodbatlas_advanced_cluster.this]
  module { source = "./" }

  variables {
    name         = "tf-test-backup-copy-replication-specs"
    project_id   = var.project_id
    cluster_type = "REPLICASET"
    regions      = []
    replication_specs = [{
      region_configs = [{
        provider_name   = "AWS"
        region_name     = "US_EAST_1"
        priority        = 7
        electable_specs = { instance_size = "M10", node_count = 3 }
      }]
    }]
    backup_copy_region = {}
  }
}

run "copy_region_geosharded_derives_from_first_zone" {
  command = plan
  module { source = "./" }

  variables {
    name          = "tf-test-backup-copy-geo"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "GEOSHARDED"
    regions = [
      { name = "US_EAST_1", node_count = 3, zone_name = "US" },
      { name = "US_WEST_2", node_count = 2, zone_name = "US" },
      { name = "EU_WEST_1", node_count = 3, zone_name = "EU" },
    ]
    backup_copy_region = {}
  }

  assert {
    condition     = module.backup_schedule[0].schedule.copy_settings[0].region_name == "US_WEST_2"
    error_message = "GEOSHARDED copy region should auto-derive from the first zone's regions"
  }
}

run "copy_region_geosharded_insufficient_regions_in_first_zone_fails" {
  command         = plan
  expect_failures = [mongodbatlas_advanced_cluster.this]
  module { source = "./" }

  variables {
    name          = "tf-test-backup-copy-geo-insufficient"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "GEOSHARDED"
    regions = [
      { name = "US_EAST_1", node_count = 3, zone_name = "US" },
      { name = "EU_WEST_1", node_count = 3, zone_name = "EU" },
      { name = "EU_WEST_2", node_count = 2, zone_name = "EU" },
    ]
    backup_copy_region = {}
  }
}

run "deletion_policy_keep_maps_to_skip_destroy" {
  command = plan
  module { source = "./" }

  variables {
    name                            = "tf-test-backup-keep"
    project_id                      = var.project_id
    provider_name                   = "AWS"
    cluster_type                    = "REPLICASET"
    regions                         = [{ name = "US_EAST_1", node_count = 3 }]
    backup_schedule_deletion_policy = "KEEP"
  }

  assert {
    condition     = module.backup_schedule[0].schedule.skip_destroy == true
    error_message = "backup_schedule_deletion_policy=KEEP should map to skip_destroy=true"
  }
}

run "backup_export_wires_export_block" {
  command = plan
  module { source = "./" }

  variables {
    name          = "tf-test-backup-export"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "REPLICASET"
    regions       = [{ name = "US_EAST_1", node_count = 3 }]
    backup_export = {
      export_bucket_id = "000000000000000000000000"
      frequency_type   = "monthly"
    }
  }

  assert {
    condition     = module.backup_schedule[0].schedule.auto_export_enabled == true
    error_message = "auto_export_enabled should be true when backup_export is set"
  }

  assert {
    condition     = module.backup_schedule[0].schedule.export[0].export_bucket_id == "000000000000000000000000"
    error_message = "export block should carry through the export_bucket_id"
  }
}
