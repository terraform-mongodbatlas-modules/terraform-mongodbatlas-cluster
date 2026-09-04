mock_provider "mongodbatlas" {}

variables {
  project_id = "000000000000000000000000"
}

run "replicaset_priorities_multiple_regions" {
  command = plan
  module { source = "./." }

  variables {
    name          = "tf-test-multi-regions"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "REPLICASET"
    regions = [
      {
        name       = "US_EAST_1",
        node_count = 2
      },
      {
        name       = "US_WEST_2",
        node_count = 2
      },
      {
        name       = "EU_WEST_1",
        node_count = 1
      },
    ]
  }

  assert {
    condition     = length(mongodbatlas_advanced_cluster.this.replication_specs) == 1
    error_message = "REPLICASET should produce exactly one replication spec"
  }

  assert {
    condition     = length(mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs) == length(var.regions)
    error_message = "region_configs count should equal number of input regions"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].priority == 7
    error_message = "first region priority should be 7"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[1].priority == 6
    error_message = "second region priority should be 6"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[2].priority == 5
    error_message = "third region priority should be 5"
  }
}

run "replicaset_priority_zero_non_electable_regions" {
  command = plan
  module { source = "./." }

  variables {
    name          = "tf-test-mixed-node-regions"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "REPLICASET"
    regions = [
      { name = "US_EAST_1", node_count = 3 },
      { name = "US_WEST_2", node_count_analytics = 2 },
      { name = "EU_WEST_1", node_count_read_only = 2 },
    ]
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].priority == 7
    error_message = "electable region priority should be 7"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[1].priority == 0
    error_message = "analytics-only region priority should be 0, got ${mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[1].priority}"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[2].priority == 0
    error_message = "read-only-only region priority should be 0, got ${mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[2].priority}"
  }
}

run "replicaset_rejects_non_electable_before_electable" {
  command = plan
  expect_failures = [
    mongodbatlas_advanced_cluster.this
  ]
  module { source = "./." }

  variables {
    name          = "tf-test-non-electable-first"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "REPLICASET"
    regions = [
      { name = "US_WEST_2", node_count_analytics = 2 },
      { name = "US_EAST_1", node_count = 3 },
    ]
  }
}

run "replicaset_rejects_non_electable_between_electable" {
  command = plan
  expect_failures = [
    mongodbatlas_advanced_cluster.this
  ]
  module { source = "./." }

  variables {
    name          = "tf-test-non-electable-interleaved"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "REPLICASET"
    regions = [
      { name = "US_EAST_1", node_count = 3 },
      { name = "US_WEST_2", node_count_analytics = 2 },
      { name = "EU_WEST_1", node_count = 2 },
    ]
  }
}

run "sharded_allows_non_electable_before_next_shard_electable" {
  command = plan
  module { source = "./." }

  variables {
    name          = "tf-test-sharded-mixed-order"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "SHARDED"
    regions = [
      { name = "US_EAST_1", node_count = 3, shard_name = "s0" },
      { name = "US_WEST_2", node_count_analytics = 2, shard_name = "s0" },
      { name = "EU_WEST_1", node_count = 3, shard_name = "s1" },
    ]
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].priority == 7
    error_message = "s0 electable region priority should be 7"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[1].priority == 0
    error_message = "s0 analytics-only region priority should be 0"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[1].region_configs[0].priority == 7
    error_message = "s1 electable region after s0 analytics should still be priority 7"
  }
}

run "geosharded_priority_zero_non_electable_regions" {
  command = plan
  module { source = "./." }

  variables {
    name          = "tf-test-geo-mixed-node-regions"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "GEOSHARDED"
    regions = [
      { name = "US_EAST_1", node_count = 3, zone_name = "US" },
      { name = "US_WEST_2", node_count_analytics = 2, zone_name = "US" },
      { name = "EU_WEST_1", node_count = 3, zone_name = "EU" },
      { name = "EU_CENTRAL_1", node_count_read_only = 2, zone_name = "EU" },
    ]
  }

  assert {
    condition     = length(mongodbatlas_advanced_cluster.this.replication_specs) == 2
    error_message = "GEOSHARDED cluster should have exactly 2 replication specs (one per zone)"
  }

  assert {
    condition     = [for spec in mongodbatlas_advanced_cluster.this.replication_specs : spec if spec.zone_name == "US"][0].region_configs[0].priority == 7
    error_message = "US zone electable region priority should be 7"
  }

  assert {
    condition     = [for spec in mongodbatlas_advanced_cluster.this.replication_specs : spec if spec.zone_name == "US"][0].region_configs[1].priority == 0
    error_message = "US zone analytics-only region priority should be 0"
  }

  assert {
    condition     = [for spec in mongodbatlas_advanced_cluster.this.replication_specs : spec if spec.zone_name == "EU"][0].region_configs[0].priority == 7
    error_message = "EU zone electable region priority should be 7"
  }

  assert {
    condition     = [for spec in mongodbatlas_advanced_cluster.this.replication_specs : spec if spec.zone_name == "EU"][0].region_configs[1].priority == 0
    error_message = "EU zone read-only-only region priority should be 0"
  }
}

run "multi_geo_zone_sharded" {
  command = plan

  module { source = "./." }

  variables {
    name          = "tf-test-multi-geo-sharded"
    project_id    = var.project_id
    cluster_type  = "GEOSHARDED"
    provider_name = "AWS"
    regions = [
      {
        name       = "US_EAST_1",
        node_count = 3
        zone_name  = "US"
      },
      {
        name       = "EU_WEST_1",
        node_count = 3
        zone_name  = "EU"
      }
    ]
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.cluster_type == "GEOSHARDED"
    error_message = "cluster_type should be GEOSHARDED"
  }

  assert {
    condition     = length(mongodbatlas_advanced_cluster.this.replication_specs) == 2
    error_message = "GEOSHARDED cluster should have exactly 2 replication specs (one per zone)"
  }

  assert {
    condition     = contains([for spec in mongodbatlas_advanced_cluster.this.replication_specs : spec.zone_name], "US")
    error_message = "GEOSHARDED cluster must include US zone"
  }

  assert {
    condition     = contains([for spec in mongodbatlas_advanced_cluster.this.replication_specs : spec.zone_name], "EU")
    error_message = "GEOSHARDED cluster must include EU zone"
  }

  assert {
    condition     = length(distinct([for spec in mongodbatlas_advanced_cluster.this.replication_specs : spec.zone_name])) == 2
    error_message = "GEOSHARDED cluster should have exactly 2 distinct zones"
  }
}
