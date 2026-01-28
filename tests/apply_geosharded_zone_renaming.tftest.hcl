run "apply_random_name" {
  module {
    source = "./tests/random_name_generator"
  }
}

run "create_project" {
  module {
    source = "./tests/project_generator"
  }

  variables {
    project_name = "test-acc-tf-p-${run.apply_random_name.name_project}" # DO NOT EDIT, prefix used by the cleanup-test-env.yml
  }
}

# Step 1: Apply the initial configuration
run "geo_zone_initial_apply" {
  command   = apply
  state_key = "geo_zone_renaming" # used to ensure state is preserved between runs

  variables {
    name          = "tf-test-geo-zone"
    project_id    = run.create_project.project_id
    provider_name = "AWS"
    cluster_type  = "GEOSHARDED"
    regions = [
      { name = "US_EAST_1", node_count = 3, zone_name = "US" },
      { name = "EU_WEST_1", node_count = 3, zone_name = "EU" }
    ]
  }
}

# Step 2: Test the plan for renaming the zone
run "geo_zone_rename_plan" {
  command   = plan
  state_key = "geo_zone_renaming" # used to ensure state is preserved between runs

  variables {
    name          = "tf-test-geo-zone"
    project_id    = run.create_project.project_id
    provider_name = "AWS"
    cluster_type  = "GEOSHARDED"
    regions = [
      { name = "US_EAST_1", node_count = 3, zone_name = "AMER" }, # zone renamed
      { name = "EU_WEST_1", node_count = 3, zone_name = "EU" }
    ]
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].zone_name == "AMER"
    error_message = "Expected renamed zone to persist"
  }
}
