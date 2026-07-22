# Verifies a real-Atlas retention edge case that the mock-provider plan tests cannot: a completely
# empty ON_DEMAND policy is accepted (confirmed below). A SCHEDULED policy that omits hourly while
# PIT is effectively enabled is rejected by Atlas ("Continuous Cloud Backup requires an hourly policy
# item", confirmed via PR #169 review discussion) -- that case is now caught at `terraform plan` by
# a backup_retention validation instead, see tests/plan_backup_schedule.tftest.hcl.
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
  command = apply

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
