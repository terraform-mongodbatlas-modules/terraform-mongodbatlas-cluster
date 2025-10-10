run "replicaset_priorities_multiple_regions" {
  command = plan
  module { source = "../" }

  variables {
    name          = "replicaset-multiple-regions"
    provider_name = "AWS"
    cluster_type  = "REPLICASET"
    regions = [
      { name = "US_EAST_1", 
        node_count = 2 
      },
      { 
        name = "US_WEST_2", 
        node_count = 2 },
      { 
        name = "EU_WEST_1", 
        node_count = 1 }
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

