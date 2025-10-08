variables {
  name          = "autoscaling-disabled"
  provider_name = "AWS"
  regions = [
    {
      name = "US_EAST_1",
    node_count = 3 }
  ]
  cluster_type = "REPLICASET"
  auto_scaling = {
    compute_enabled = false
  }
}

run "autoscaling_disabled" {
  command = plan

  module {
    source = "../"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].auto_scaling.compute_enabled == false
    error_message = "Expected mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].auto_scaling.compute_enabled to be false"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].auto_scaling.compute_min_instance_size != null
    error_message = "Expected mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].auto_scaling.compute_min_instance_size to be null"
  }
  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].auto_scaling.compute_max_instance_size != null
    error_message = "Expected mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].auto_scaling.compute_max_instance_size to be null"
  }
  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].auto_scaling.compute_scale_down_enabled != null
    error_message = "Expected mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].auto_scaling.compute_scale_down_enabled to be null"
  }
}