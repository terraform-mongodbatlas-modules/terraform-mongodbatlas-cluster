run "autoscaling_enabled_default" {
  command = plan

  module {
    source = "../"
  }

  variables {
    name          = "tf-test-autoscaling-enabled"
    project_id    = var.project_id
    provider_name = "AWS"
    regions = [
      {
        name       = "US_EAST_1",
        node_count = 3
      }
    ]
    cluster_type = "REPLICASET"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].auto_scaling.compute_enabled == true
    error_message = "Expected mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].auto_scaling.compute_enabled to be true"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].auto_scaling.disk_gb_enabled == true
    error_message = "Expected mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].auto_scaling.compute_enabled to be true"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].auto_scaling.compute_min_instance_size == "M10"
    error_message = "Expected mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].auto_scaling.compute_min_instance_size to be M10"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].auto_scaling.compute_max_instance_size == "M200"
    error_message = "Expected mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].auto_scaling.compute_max_instance_size to be M200"
  }
}

run "autoscaling_disabled" {
  command = plan

  module {
    source = "../"
  }

  variables {
    name          = "tf-test-autoscaling-disabled"
    project_id    = var.project_id
    provider_name = "AWS"
    instance_size = "M10"
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

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].auto_scaling.compute_enabled == false
    error_message = "Expected mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].auto_scaling.compute_enabled to be false"
  }
  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].electable_specs.instance_size == "M10"
    error_message = "Expected mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].electable_specs.instance_size to be M10"
  }
}