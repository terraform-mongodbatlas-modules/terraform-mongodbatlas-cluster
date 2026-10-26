# Verifies a two-region cluster can drop every cross-region copy target without Atlas rejecting the
# one-way copy_policy_items_enabled flag: `backup_copy_region = { region_count = 0 }` keeps the flag
# true and sends an empty copy_settings. Removing `backup_copy_region` outright would send false and fail.
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

run "create_cluster_with_copy_region" {
  command = apply
  module { source = "./." }

  variables {
    name          = "tf-test-copy-removal"
    project_id    = run.create_project.project_id
    cluster_type  = "REPLICASET"
    provider_name = "AWS"
    regions = [
      { name = "US_EAST_1", node_count = 3, instance_size = "M10" },
      { name = "US_WEST_2", node_count = 2, instance_size = "M10" },
    ]
    auto_scaling = {
      compute_enabled = false
    }
    backup_copy_region = {}
  }

  assert {
    condition     = length(module.backup_schedule[0].schedule.copy_settings) == 1
    error_message = "backup_copy_region = {} should derive one copy target"
  }

  assert {
    condition     = module.backup_schedule[0].schedule.copy_policy_items_enabled == true
    error_message = "copy_policy_items_enabled should be true once a copy target exists"
  }
}

run "remove_copy_targets_keeps_flag" {
  command = apply
  module { source = "./." }

  variables {
    name          = "tf-test-copy-removal"
    project_id    = run.create_project.project_id
    cluster_type  = "REPLICASET"
    provider_name = "AWS"
    regions = [
      { name = "US_EAST_1", node_count = 3, instance_size = "M10" },
      { name = "US_WEST_2", node_count = 2, instance_size = "M10" },
    ]
    auto_scaling = {
      compute_enabled = false
    }
    backup_copy_region = { region_count = 0 }
  }

  assert {
    condition     = length(module.backup_schedule[0].schedule.copy_settings) == 0
    error_message = "region_count = 0 should drop every copy target"
  }

  assert {
    condition     = module.backup_schedule[0].schedule.copy_policy_items_enabled == true
    error_message = "copy_policy_items_enabled must stay true so Atlas accepts the copy-settings removal"
  }
}
