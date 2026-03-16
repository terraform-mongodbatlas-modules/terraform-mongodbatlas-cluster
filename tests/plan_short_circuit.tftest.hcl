/* Verify that trimspace(null) does not crash on TF 1.9-1.11 where && / || inside
   for expressions do not short-circuit. Each run block maps to a broken config
   from the investigation (see t11-01 prompt). */
mock_provider "mongodbatlas" {}

variables {
  project_id = "000000000000000000000000"
}

run "replicaset_null_zone_name" {
  command = plan
  module { source = "./" }

  variables {
    name          = "tf-test-rs-null-zone"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "REPLICASET"
    regions       = [{ name = "US_WEST_2", node_count = 3 }]
  }

  assert {
    condition     = length(mongodbatlas_advanced_cluster.this.replication_specs) == 1
    error_message = "REPLICASET with null zone_name should plan without crash"
  }
}

run "sharded_uniform_null_zone_name" {
  command = plan
  module { source = "./" }

  variables {
    name          = "tf-test-sharded-null-zone"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "SHARDED"
    shard_count   = 2
    regions       = [{ name = "US_EAST_1", node_count = 3 }]
  }

  assert {
    condition     = length(mongodbatlas_advanced_cluster.this.replication_specs) == 2
    error_message = "SHARDED with null zone_name should plan without crash"
  }
}

run "sharded_explicit_null_zone_name" {
  command = plan
  module { source = "./" }

  variables {
    name          = "tf-test-sharded-explicit-null-zone"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "SHARDED"
    regions = [
      { name = "US_EAST_1", node_count = 3, shard_number = 0 },
      { name = "US_WEST_2", node_count = 3, shard_number = 1 },
    ]
  }

  assert {
    condition     = length(mongodbatlas_advanced_cluster.this.replication_specs) == 2
    error_message = "SHARDED explicit with null zone_name should plan without crash"
  }
}

run "geosharded_missing_zone_name_validation" {
  command = plan
  expect_failures = [
    mongodbatlas_advanced_cluster.this
  ]
  module { source = "./" }

  variables {
    name          = "tf-test-geo-null-zone"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "GEOSHARDED"
    regions       = [{ name = "US_EAST_1", node_count = 3 }]
  }
}
