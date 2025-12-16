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

  assert {
    condition     = length(mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs) == 1
    error_message = "Expected US(0) to have 1 region_config"
  }

  assert {
    condition     = length(mongodbatlas_advanced_cluster.this.replication_specs[1].region_configs) == 1
    error_message = "Expected US(1) to have 1 region_config"
  }

  assert {
    condition     = length(mongodbatlas_advanced_cluster.this.replication_specs[2].region_configs) == 1
    error_message = "Expected EU(0) to have 1 region_config"
  }
}

run "geo_multi_regions_in_same_shard" {
  command = plan

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
