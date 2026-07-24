mock_provider "mongodbatlas" {}

variables {
  project_id = "000000000000000000000000"
}
run "geo_single_shard_per_zone_order" {
  command = plan

  module {
    source = "./"
  }

  variables {
    name          = "tf-test-geo-single"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "GEOSHARDED"

    regions = [
      { name = "US_EAST_1", node_count = 3, zone_name = "US" },
      { name = "EU_WEST_1", node_count = 3, zone_name = "EU" },
    ]
  }

  assert {
    condition     = length(mongodbatlas_advanced_cluster.this.replication_specs) == 2
    error_message = "Expected exactly 2 replication_specs for 2 zones"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].zone_name == "US"
    error_message = "Expected first replication_spec zone_name to be US"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[1].zone_name == "EU"
    error_message = "Expected second replication_spec zone_name to be EU"
  }

  assert {
    condition     = length(mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs) == 1
    error_message = "Expected US group to have 1 region_config"
  }

  assert {
    condition     = length(mongodbatlas_advanced_cluster.this.replication_specs[1].region_configs) == 1
    error_message = "Expected EU group to have 1 region_config"
  }
}

run "geo_multi_shards_in_zone" {
  command = plan
  expect_failures = [
    check.shard_number_deprecated
  ]


  module {
    source = "./"
  }

  variables {
    name          = "tf-test-geo-multi-shards"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "GEOSHARDED"

    regions = [
      { name = "US_EAST_1", node_count = 3, zone_name = "US", shard_number = 0 },
      { name = "US_WEST_1", node_count = 3, zone_name = "US", shard_number = 1 },
      { name = "EU_WEST_1", node_count = 3, zone_name = "EU", shard_number = 0 },
    ]
  }

  assert {
    condition     = length(mongodbatlas_advanced_cluster.this.replication_specs) == 3
    error_message = "Expected 3 replication_specs for US(0), US(1), EU(0)"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].zone_name == "US"
    error_message = "Expected replication_specs[0] zone_name to be US"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[1].zone_name == "US"
    error_message = "Expected replication_specs[1] zone_name to be US"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[2].zone_name == "EU"
    error_message = "Expected replication_specs[2] zone_name to be EU"
  }
}

run "geo_shard_name_multi_shard_and_order" {
  command = plan

  module {
    source = "./"
  }

  variables {
    name          = "tf-test-geo-shard-name"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "GEOSHARDED"

    regions = [
      { name = "US_WEST_1", node_count = 3, zone_name = "US", shard_name = "us1" },
      { name = "US_EAST_1", node_count = 3, zone_name = "US", shard_name = "us0" },
      { name = "EU_WEST_1", node_count = 3, zone_name = "EU", shard_name = "eu0" },
    ]
  }

  assert {
    condition = (
      length(mongodbatlas_advanced_cluster.this.replication_specs) == 3 &&
      mongodbatlas_advanced_cluster.this.replication_specs[0].zone_name == "US" &&
      mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].region_name == "US_WEST_1" &&
      mongodbatlas_advanced_cluster.this.replication_specs[1].zone_name == "US" &&
      mongodbatlas_advanced_cluster.this.replication_specs[1].region_configs[0].region_name == "US_EAST_1" &&
      mongodbatlas_advanced_cluster.this.replication_specs[2].zone_name == "EU"
    )
    error_message = "Named geo shards should follow first appearance within each zone (us1 then us0), then next zone"
  }
}

run "geo_shard_number_first_appearance_order_within_zone" {
  command = plan
  expect_failures = [
    check.shard_number_deprecated
  ]


  module {
    source = "./"
  }

  variables {
    name          = "tf-test-geo-number-order"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "GEOSHARDED"

    regions = [
      { name = "US_WEST_1", node_count = 3, zone_name = "US", shard_number = 1 },
      { name = "US_EAST_1", node_count = 3, zone_name = "US", shard_number = 0 },
      { name = "EU_WEST_1", node_count = 3, zone_name = "EU", shard_number = 0 },
    ]
  }

  assert {
    condition = (
      length(mongodbatlas_advanced_cluster.this.replication_specs) == 3 &&
      mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].region_name == "US_WEST_1" &&
      mongodbatlas_advanced_cluster.this.replication_specs[1].region_configs[0].region_name == "US_EAST_1" &&
      mongodbatlas_advanced_cluster.this.replication_specs[2].zone_name == "EU"
    )
    error_message = "Within a zone, shard_number groups should follow first appearance in regions (1 then 0 as listed)"
  }
}

run "geo_rejects_duplicate_shard_name_across_zones" {
  command = plan
  expect_failures = [
    mongodbatlas_advanced_cluster.this
  ]

  module {
    source = "./"
  }

  variables {
    name          = "tf-test-geo-dup-name"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "GEOSHARDED"

    regions = [
      { name = "US_EAST_1", node_count = 3, zone_name = "US", shard_name = "s0" },
      { name = "EU_WEST_1", node_count = 3, zone_name = "EU", shard_name = "s0" },
    ]
  }
}

run "geo_multi_regions_in_same_shard" {
  command = plan
  expect_failures = [
    check.shard_number_deprecated
  ]


  module {
    source = "./"
  }

  variables {
    name          = "tf-test-geo-multi-regions-same-shard"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "GEOSHARDED"

    regions = [
      { name = "US_EAST_1", node_count = 3, zone_name = "US", shard_number = 0 },
      { name = "US_WEST_2", node_count = 2, zone_name = "US", shard_number = 0 },
      { name = "EU_WEST_1", node_count = 3, zone_name = "EU", shard_number = 0 },
    ]
  }

  assert {
    condition     = length(mongodbatlas_advanced_cluster.this.replication_specs) == 2
    error_message = "Expected 2 replication_specs for US(0) and EU(0)"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].zone_name == "US"
    error_message = "Expected first spec zone_name to be US"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[1].zone_name == "EU"
    error_message = "Expected second spec zone_name to be EU"
  }

  assert {
    condition     = length(mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs) == 2
    error_message = "Expected US(0) to have 2 region_configs"
  }

  assert {
    condition     = length(mongodbatlas_advanced_cluster.this.replication_specs[1].region_configs) == 1
    error_message = "Expected EU(0) to have 1 region_config"
  }
}

run "geo_uniform_layout" {
  command = plan

  module {
    source = "./"
  }

  variables {
    name          = "tf-test-geo-uniform"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "GEOSHARDED"
    geoshard_counts = {
      US = 2
      EU = 3
    }
    regions = [
      { name = "US_EAST_1", node_count = 3, zone_name = "US" },
      { name = "US_WEST_2", node_count = 2, zone_name = "US" },
      { name = "EU_WEST_1", node_count = 3, zone_name = "EU" },
      { name = "EU_NORTH_1", node_count = 3, zone_name = "EU" },
    ]
  }

  assert {
    condition = (
      length(mongodbatlas_advanced_cluster.this.replication_specs) == 5 &&
      mongodbatlas_advanced_cluster.this.replication_specs[0].zone_name == "US" &&
      mongodbatlas_advanced_cluster.this.replication_specs[1].zone_name == "US" &&
      mongodbatlas_advanced_cluster.this.replication_specs[2].zone_name == "EU" &&
      mongodbatlas_advanced_cluster.this.replication_specs[3].zone_name == "EU" &&
      mongodbatlas_advanced_cluster.this.replication_specs[4].zone_name == "EU" &&
      length(mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs) == 2 &&
      mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].region_name == "US_EAST_1" &&
      mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[1].region_name == "US_WEST_2" &&
      mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].priority == 7 &&
      mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[1].priority == 6 &&
      length(mongodbatlas_advanced_cluster.this.replication_specs[2].region_configs) == 2
    )
    error_message = "Uniform geo should expand US×2 then EU×3 with duplicated region layouts"
  }
}

run "geo_uniform_rejects_shard_name" {
  command = plan
  expect_failures = [
    mongodbatlas_advanced_cluster.this
  ]

  module {
    source = "./"
  }

  variables {
    name          = "tf-test-geo-uniform-name"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "GEOSHARDED"
    geoshard_counts = {
      US = 2
      EU = 1
    }
    regions = [
      { name = "US_EAST_1", node_count = 3, zone_name = "US", shard_name = "us0" },
      { name = "EU_WEST_1", node_count = 3, zone_name = "EU" },
    ]
  }
}

run "geo_uniform_rejects_missing_zone" {
  command = plan
  expect_failures = [
    mongodbatlas_advanced_cluster.this
  ]

  module {
    source = "./"
  }

  variables {
    name          = "tf-test-geo-uniform-missing"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "GEOSHARDED"
    geoshard_counts = {
      US = 2
    }
    regions = [
      { name = "US_EAST_1", node_count = 3, zone_name = "US" },
      { name = "EU_WEST_1", node_count = 3, zone_name = "EU" },
    ]
  }
}

run "geo_uniform_rejects_extra_zone" {
  command = plan
  expect_failures = [
    mongodbatlas_advanced_cluster.this
  ]

  module {
    source = "./"
  }

  variables {
    name          = "tf-test-geo-uniform-extra"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "GEOSHARDED"
    geoshard_counts = {
      US = 2
      EU = 1
      AP = 1
    }
    regions = [
      { name = "US_EAST_1", node_count = 3, zone_name = "US" },
      { name = "EU_WEST_1", node_count = 3, zone_name = "EU" },
    ]
  }
}

run "geoshard_counts_zero_invalid" {
  command = plan
  expect_failures = [
    var.geoshard_counts
  ]

  module {
    source = "./"
  }

  variables {
    name          = "tf-test-geo-counts-zero"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "GEOSHARDED"
    geoshard_counts = {
      US = 0
    }
    regions = [
      { name = "US_EAST_1", node_count = 3, zone_name = "US" },
    ]
  }
}

run "geoshard_counts_wrong_cluster_type" {
  command = plan
  expect_failures = [
    var.geoshard_counts
  ]

  module {
    source = "./"
  }

  variables {
    name          = "tf-test-geo-counts-sharded"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "SHARDED"
    geoshard_counts = {
      US = 2
    }
    regions = [
      { name = "US_EAST_1", node_count = 3, shard_name = "s0" },
    ]
  }
}
