mock_provider "mongodbatlas" {}

variables {
  project_id = "000000000000000000000000"
}

run "default_is_atlas_managed" {
  command = plan
  module { source = "./" }

  variables {
    name          = "tf-test-config-server-default"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "SHARDED"
    shard_count   = 1
    regions       = [{ name = "US_EAST_1", node_count = 3 }]
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.config_server_management_mode == "ATLAS_MANAGED"
    error_message = "config_server_management_mode should default to ATLAS_MANAGED"
  }
}

run "fixed_to_dedicated_escape_hatch" {
  command = plan
  module { source = "./" }

  variables {
    name                          = "tf-test-config-server-fixed"
    project_id                    = var.project_id
    provider_name                 = "AWS"
    cluster_type                  = "SHARDED"
    shard_count                   = 1
    regions                       = [{ name = "US_EAST_1", node_count = 3 }]
    config_server_management_mode = "FIXED_TO_DEDICATED"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.config_server_management_mode == "FIXED_TO_DEDICATED"
    error_message = "config_server_management_mode should honor FIXED_TO_DEDICATED"
  }
}

run "null_zero_diff_upgrade_path_is_accepted" {
  command = plan
  module { source = "./" }

  variables {
    name                          = "tf-test-config-server-null"
    project_id                    = var.project_id
    provider_name                 = "AWS"
    cluster_type                  = "SHARDED"
    shard_count                   = 1
    regions                       = [{ name = "US_EAST_1", node_count = 3 }]
    config_server_management_mode = null
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.cluster_type == "SHARDED"
    error_message = "config_server_management_mode = null (zero-diff upgrade path) should validate and plan"
  }
}

run "invalid_value_fails_validation" {
  command = plan
  module { source = "./" }

  variables {
    name                          = "tf-test-config-server-invalid"
    project_id                    = var.project_id
    provider_name                 = "AWS"
    cluster_type                  = "SHARDED"
    shard_count                   = 1
    regions                       = [{ name = "US_EAST_1", node_count = 3 }]
    config_server_management_mode = "INVALID"
  }

  expect_failures = [
    var.config_server_management_mode
  ]
}
