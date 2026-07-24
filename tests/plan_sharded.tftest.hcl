mock_provider "mongodbatlas" {}

variables {
  project_id = "000000000000000000000000"
}

run "sharded_uniform_layout_and_priorities" {
  command = plan
  module {
    source = "./"
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
    mongodbatlas_advanced_cluster.this,
    check.shard_number_deprecated,
  ]

  module {
    source = "./"
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

run "sharded_uniform_conflicts_with_shard_name" {
  command = plan
  expect_failures = [
    mongodbatlas_advanced_cluster.this
  ]

  module {
    source = "./"
  }

  variables {
    name          = "tf-test-sharded-conflict-name"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "SHARDED"

    shard_count = 2
    regions = [
      { name = "US_EAST_1", node_count = 3, shard_name = "s0" },
    ]
  }
}

run "sharded_explicit_requires_identity" {
  command = plan
  expect_failures = [
    mongodbatlas_advanced_cluster.this
  ]

  module {
    source = "./"
  }

  variables {
    name          = "tf-test-sharded-explicit-missing"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "SHARDED"

    regions = [
      { name = "US_EAST_1", node_count = 3 },
      { name = "US_WEST_2", node_count = 3, shard_name = "s1" },
    ]
  }
}

run "sharded_shard_name_grouping_and_order" {
  command = plan

  module {
    source = "./"
  }

  variables {
    name          = "tf-test-sharded-name-order"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "SHARDED"

    regions = [
      { name = "US_EAST_1", node_count = 3, shard_name = "b" },
      { name = "US_WEST_2", node_count = 2, shard_name = "b" },
      { name = "EU_WEST_1", node_count = 3, shard_name = "a" },
    ]
  }

  assert {
    condition     = length(mongodbatlas_advanced_cluster.this.replication_specs) == 2
    error_message = "Expected 2 shards for names b and a"
  }

  assert {
    condition = (
      length(mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs) == 2 &&
      mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].region_name == "US_EAST_1" &&
      length(mongodbatlas_advanced_cluster.this.replication_specs[1].region_configs) == 1 &&
      mongodbatlas_advanced_cluster.this.replication_specs[1].region_configs[0].region_name == "EU_WEST_1"
    )
    error_message = "shard_name groups should follow first appearance (b then a), not lexicographic order"
  }
}

run "sharded_shard_number_first_appearance_order" {
  command = plan
  expect_failures = [
    check.shard_number_deprecated
  ]

  module {
    source = "./"
  }

  variables {
    name          = "tf-test-sharded-number-order"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "SHARDED"

    regions = [
      { name = "US_WEST_2", node_count = 3, shard_number = 1 },
      { name = "US_EAST_1", node_count = 3, shard_number = 0 },
    ]
  }

  assert {
    condition = (
      length(mongodbatlas_advanced_cluster.this.replication_specs) == 2 &&
      mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].region_name == "US_WEST_2" &&
      mongodbatlas_advanced_cluster.this.replication_specs[1].region_configs[0].region_name == "US_EAST_1"
    )
    error_message = "shard_number groups should follow first appearance in regions (1 then 0 as listed)"
  }
}

run "sharded_rejects_both_fields_on_region" {
  command = plan
  expect_failures = [
    var.regions
  ]

  module {
    source = "./"
  }

  variables {
    name          = "tf-test-sharded-both-fields"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "SHARDED"

    regions = [
      { name = "US_EAST_1", node_count = 3, shard_name = "s0", shard_number = 0 },
    ]
  }
}

run "sharded_rejects_invalid_shard_name" {
  command = plan
  expect_failures = [
    var.regions
  ]

  module {
    source = "./"
  }

  variables {
    name          = "tf-test-sharded-bad-name"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "SHARDED"

    regions = [
      { name = "US_EAST_1", node_count = 3, shard_name = "0" },
    ]
  }
}

run "sharded_rejects_mixed_field_family" {
  command = plan
  expect_failures = [
    mongodbatlas_advanced_cluster.this,
    check.shard_number_deprecated,
  ]

  module {
    source = "./"
  }

  variables {
    name          = "tf-test-sharded-mixed-family"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "SHARDED"

    regions = [
      { name = "US_EAST_1", node_count = 3, shard_name = "s0" },
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
    source = "./"
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
    source = "./"
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
