# Verifies two retention edge cases against real Atlas that the mock-provider plan tests cannot:
# whether Atlas accepts a completely empty ON_DEMAND policy, and whether it accepts a partial
# SCHEDULED policy that omits hourly while PIT is enabled. Per the Atlas docs, a PIT restore window
# cannot be longer than the hourly snapshot retention time, so omitting hourly entirely while PIT
# is enabled is an open question (see PR #169 review discussion).
#
# If either case is rejected by Atlas, add cross-variable validation so it fails at `terraform plan`
# instead of at apply.
#
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

# Step 1: ON_DEMAND mode with a completely empty policy (no frequency-based policy items at all),
# PIT enabled (the default when backup_enabled = true).
run "on_demand_empty_policy_with_pit_enabled" {
  command   = apply
  state_key = "retention_edge_cases" # used to ensure state is preserved between runs

  variables {
    name          = "tf-test-retention-edge"
    project_id    = run.create_project.project_id
    cluster_type  = "REPLICASET"
    provider_name = "AWS"
    regions = [
      { name = "US_EAST_1", node_count = 3, instance_size = "M10" },
    ]
    auto_scaling = {
      compute_enabled = false
    }
    backup_mode = "ON_DEMAND"
  }

  assert {
    condition     = length(module.backup_schedule) == 1
    error_message = "backup_schedule submodule should be created for ON_DEMAND mode"
  }

  assert {
    condition = alltrue([
      length(module.backup_schedule[0].schedule.policy_item_hourly) == 0,
      length(module.backup_schedule[0].schedule.policy_item_daily) == 0,
      length(module.backup_schedule[0].schedule.policy_item_weekly) == 0,
      length(module.backup_schedule[0].schedule.policy_item_monthly) == 0,
      length(module.backup_schedule[0].schedule.policy_item_yearly) == 0,
    ])
    error_message = "ON_DEMAND mode should result in a schedule with no frequency-based policy items"
  }
}

# Step 2: reconfigure the same cluster to SCHEDULED mode with only a daily policy (hourly omitted via
# skip_default_retentions), PIT still enabled by default.
run "scheduled_daily_only_without_hourly_with_pit_enabled" {
  command   = apply
  state_key = "retention_edge_cases" # used to ensure state is preserved between runs

  variables {
    name          = "tf-test-retention-edge"
    project_id    = run.create_project.project_id
    cluster_type  = "REPLICASET"
    provider_name = "AWS"
    regions = [
      { name = "US_EAST_1", node_count = 3, instance_size = "M10" },
    ]
    auto_scaling = {
      compute_enabled = false
    }
    backup_mode = "SCHEDULED"
    backup_retention = {
      skip_default_retentions = true
      daily                   = { retention_value = 14 }
    }
  }

  assert {
    condition     = length(module.backup_schedule[0].schedule.policy_item_hourly) == 0
    error_message = "hourly policy should be omitted when skip_default_retentions = true and hourly is not set"
  }

  assert {
    condition     = module.backup_schedule[0].schedule.policy_item_daily[0].retention_value == 14
    error_message = "daily policy should be created with the configured retention_value"
  }
}
