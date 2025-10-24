mock_provider "mongodbatlas" {}

variables {
  project_id = "000000000000000000000000"
}

run "replicaset_priorities_multiple_regions" {
  command = plan
  module { source = "../" }

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

run "multi_geo_zone_sharded" {
  command = plan

  module { source = "../" }

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