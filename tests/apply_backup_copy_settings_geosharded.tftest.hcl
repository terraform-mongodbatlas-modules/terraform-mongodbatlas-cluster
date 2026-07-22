# Verifies copy_settings.zone_id against real Atlas on a multi-zone GEOSHARDED cluster.
# Requires real Atlas credentials -- creates a real M10 cluster, not part of unit-plan-tests.
#
# copy_settings.zone_id is Optional/Computed in the provider schema, but the underlying Atlas API
# uses it to disambiguate which zone a copy target belongs to. This confirms the module's derived
# zone_id is accepted by Atlas and matches the zone backup_copy_region auto-derives region/provider
# from (the first zone).

run "generate_name" {
  module { source = "./tests/random_name_generator" }
}

run "create_project" {
  module { source = "./tests/project_generator" }

  variables {
    project_name = "test-acc-tf-p-${run.generate_name.name_project}" # DO NOT EDIT, prefix used by cleanup-test-env.yml
  }
}

run "create_geosharded_cluster_with_copy_settings" {
  command = apply
  module { source = "./." }

  variables {
    name          = "tf-test-geo-copy-settings"
    project_id    = run.create_project.project_id
    cluster_type  = "GEOSHARDED"
    provider_name = "AWS"
    regions = [
      { name = "US_EAST_1", node_count = 3, zone_name = "US", instance_size = "M10" },
      { name = "US_WEST_2", node_count = 2, zone_name = "US", instance_size = "M10" },
      { name = "EU_WEST_1", node_count = 3, zone_name = "EU", instance_size = "M10" },
    ]
    auto_scaling = {
      compute_enabled = false
    }
    backup_copy_region = {}
  }

  assert {
    condition     = length(module.backup_schedule) == 1
    error_message = "backup_schedule submodule should be created"
  }

  assert {
    condition     = length(module.backup_schedule[0].schedule.copy_settings) == 1
    error_message = "copy_settings should be created for the auto-derived copy target"
  }

  assert {
    condition     = module.backup_schedule[0].schedule.copy_settings[0].region_name == "US_WEST_2"
    error_message = "copy target should auto-derive from the first zone's (US) regions"
  }

  assert {
    condition     = module.backup_schedule[0].schedule.copy_settings[0].zone_id == mongodbatlas_advanced_cluster.this.replication_specs[0].zone_id
    error_message = "copy_settings.zone_id should match the first zone's zone_id"
  }

  assert {
    condition     = module.backup_schedule[0].schedule.copy_settings[0].zone_id != ""
    error_message = "copy_settings.zone_id should not be empty on a multi-zone cluster -- Atlas must accept the explicitly-derived zone_id"
  }
}
