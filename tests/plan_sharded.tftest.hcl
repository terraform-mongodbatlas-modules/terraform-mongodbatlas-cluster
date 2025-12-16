run "sharded_uniform_layout_and_priorities" {
  command = plan
  module {
    source = "../"
  }

  variables {
    name          = "tf-test-sharded-uniform-3"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "SHARDED"

    shard_count = 3
    regions = [
      { name = "US_EAST_1", node_count = 3 }, # priority 7
      { name = "US_WEST_2", node_count = 3 }, # priority 6
      { name = "EU_WEST_1", node_count = 3 }, # priority 5
    ]
  }

  assert {
    condition     = length(mongodbatlas_advanced_cluster.this.replication_specs) == 3
    error_message = "Expected 3 replication_specs when shard_count=3"
  }

  assert {
    condition = (
      length(mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs) == 3 &&
      length(mongodbatlas_advanced_cluster.this.replication_specs[1].region_configs) == 3 &&
      length(mongodbatlas_advanced_cluster.this.replication_specs[2].region_configs) == 3 &&
      mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].region_name == "US_EAST_1" &&
      mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[1].region_name == "US_WEST_2" &&
      mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[2].region_name == "EU_WEST_1" &&
      mongodbatlas_advanced_cluster.this.replication_specs[1].region_configs[0].region_name == "US_EAST_1" &&
      mongodbatlas_advanced_cluster.this.replication_specs[1].region_configs[1].region_name == "US_WEST_2" &&
      mongodbatlas_advanced_cluster.this.replication_specs[1].region_configs[2].region_name == "EU_WEST_1" &&
      mongodbatlas_advanced_cluster.this.replication_specs[2].region_configs[0].region_name == "US_EAST_1" &&
      mongodbatlas_advanced_cluster.this.replication_specs[2].region_configs[1].region_name == "US_WEST_2" &&
      mongodbatlas_advanced_cluster.this.replication_specs[2].region_configs[2].region_name == "EU_WEST_1"
    )
    error_message = "Uniform shards should duplicate the same region layout"
  }
  assert {
    condition = (
      mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].priority == 7 &&
      mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[1].priority == 6 &&
      mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[2].priority == 5
    )
    error_message = "Priorities should follow input order: 7,6,5 within each shard"
  }
}

run "sharded_uniform_conflicts_with_shard_number" {
  command = plan
  expect_failures = [
    mongodbatlas_advanced_cluster.this
  ]

  module {
    source = "../"
  }

  variables {
    name          = "tf-test-sharded-conflict"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "SHARDED"

    shard_count = 2
    regions = [
      { name = "US_EAST_1", node_count = 3, shard_number = 0 },
    ]
  }
}

run "sharded_explicit_requires_shard_number" {
  command = plan
  expect_failures = [
    mongodbatlas_advanced_cluster.this
  ]

  module {
    source = "../"
  }

  variables {
    name          = "tf-test-sharded-explicit-missing"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "SHARDED"

    regions = [
      { name = "US_EAST_1", node_count = 3 }, # missing shard_number
      { name = "US_WEST_2", node_count = 3, shard_number = 1 },
    ]
  }
}

run "shard_count_zero_invalid" {
  command = plan
  expect_failures = [
    var.shard_count
  ]

  module {
    source = "../"
  }

  variables {
    name          = "tf-test-sharded-count-zero"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "SHARDED"

    shard_count = 0
    regions = [
      { name = "US_EAST_1", node_count = 3 },
    ]
  }
}

run "sharded_uniform_shard_count_one" {
  command = plan

  module {
    source = "../"
  }

  variables {
    name          = "tf-test-sharded-count-one"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "SHARDED"

    shard_count = 1
    regions = [
      { name = "US_EAST_1", node_count = 3 },
      { name = "US_WEST_2", node_count = 3 },
    ]
  }

  assert {
    condition     = length(mongodbatlas_advanced_cluster.this.replication_specs) == 1
    error_message = "Expected exactly one replication_spec when shard_count=1"
  }
}

run "sharded_uniform_shard_count_five" {
  command = plan

  module {
    source = "../"
  }

  variables {
    name          = "tf-test-sharded-count-five"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "SHARDED"

    shard_count = 5
    regions = [
      { name = "US_EAST_1", node_count = 3 },
    ]
  }

  assert {
    condition     = length(mongodbatlas_advanced_cluster.this.replication_specs) == 5
    error_message = "Expected 5 replication_specs when shard_count=5"
  }
}
