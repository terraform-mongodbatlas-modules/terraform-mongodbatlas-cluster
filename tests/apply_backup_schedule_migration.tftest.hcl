# Verifies the two-apply SCHEDULED -> UNMANAGED+KEEP migration actually skips the Atlas delete call.
# Requires real Atlas credentials -- creates a real M10 cluster, not part of unit-plan-tests.

run "generate_name" {
  module { source = "./tests/random_name_generator" }
}

run "create_project" {
  module { source = "./tests/project_generator" }

  variables {
    project_name = "test-acc-tf-p-${run.generate_name.name_project}" # DO NOT EDIT, prefix used by cleanup-test-env.yml
  }
}

run "create_cluster_with_scheduled_backup" {
  command = apply
  module { source = "./." }

  variables {
    name          = "tf-test-backup-migration"
    project_id    = run.create_project.project_id
    cluster_type  = "REPLICASET"
    provider_name = "AWS"
    regions = [{
      name          = "US_EAST_1"
      node_count    = 3
      instance_size = "M10"
    }]
    auto_scaling = {
      compute_enabled = false
    }
    backup_retention = {
      daily = { retention_value = 7 }
    }
  }

  assert {
    condition     = length(module.backup_schedule) == 1
    error_message = "backup_schedule submodule should be created"
  }

  assert {
    condition     = module.backup_schedule[0].schedule.skip_destroy == false
    error_message = "skip_destroy should be false with the default backup_schedule_skip_destroy=false"
  }
}

run "set_skip_destroy_to_true" {
  command = apply
  module { source = "./." }

  variables {
    name          = "tf-test-backup-migration"
    project_id    = run.create_project.project_id
    cluster_type  = "REPLICASET"
    provider_name = "AWS"
    regions = [{
      name          = "US_EAST_1"
      node_count    = 3
      instance_size = "M10"
    }]
    auto_scaling = {
      compute_enabled = false
    }
    backup_retention = {
      daily = { retention_value = 7 }
    }
    backup_schedule_skip_destroy = true
  }

  assert {
    condition     = length(module.backup_schedule) == 1
    error_message = "backup_schedule submodule should still be present (backup_mode unchanged)"
  }

  assert {
    condition     = module.backup_schedule[0].schedule.skip_destroy == true
    error_message = "skip_destroy should now be true in state (in-place update, resource still exists)"
  }
}

run "switch_to_unmanaged" {
  command = apply
  module { source = "./." }

  variables {
    name          = "tf-test-backup-migration"
    project_id    = run.create_project.project_id
    cluster_type  = "REPLICASET"
    provider_name = "AWS"
    regions = [{
      name          = "US_EAST_1"
      node_count    = 3
      instance_size = "M10"
    }]
    auto_scaling = {
      compute_enabled = false
    }
    backup_mode                  = "UNMANAGED"
    backup_schedule_skip_destroy = true
  }

  assert {
    condition     = length(module.backup_schedule) == 0
    error_message = "backup_schedule submodule should be gone from state after switching to UNMANAGED"
  }
}

run "verify_schedule_still_exists_in_atlas" {
  command = apply
  module { source = "./tests/backup_schedule_reader" }

  variables {
    project_id   = run.create_project.project_id
    cluster_name = "tf-test-backup-migration"
  }

  assert {
    condition     = length(data.mongodbatlas_cloud_backup_schedule.this.policy_item_daily) == 1
    error_message = "schedule should still exist in Atlas with its daily policy intact -- skip_destroy must have prevented the actual deletion when backup_mode switched to UNMANAGED"
  }

  assert {
    condition     = data.mongodbatlas_cloud_backup_schedule.this.policy_item_daily[0].retention_value == 7
    error_message = "surviving schedule should still have the retention_value configured before the migration"
  }
}
