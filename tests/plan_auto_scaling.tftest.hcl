mock_provider "mongodbatlas" {}

variables {
  project_id = "000000000000000000000000"
}

run "autoscaling_enabled_default" {
  command = plan

  module {
    source = "./"
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
    source = "./"
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

run "autoscaling_analytics_disabled_when_using_manual_scaling" {
  command = plan

  module {
    source = "./."
  }
  variables {
    name          = "single-region-with-analytics2"
    project_id    = var.project_id
    cluster_type  = "SHARDED"
    provider_name = "AWS"
    regions = [
      {
        name                    = "US_EAST_1"
        node_count              = 3 # electable auto-scaled
        shard_number            = 1
        node_count_analytics    = 1
        instance_size_analytics = "M10" # use only M10 (less than M30) for analytics node
      }
    ]
    # Override auto-scaling to use M30 as minimum
    auto_scaling = {
      compute_enabled            = true
      compute_max_instance_size  = "M50"
      compute_min_instance_size  = "M30"
      compute_scale_down_enabled = true
      disk_gb_enabled            = true
    }
  }
  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].analytics_auto_scaling.compute_enabled == false
    error_message = "Expected mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].analytics_auto_scaling.compute_enabled to be false"
  }
}

run "scale_down_disabled_should_not_set_compute_min_instance_size" {
  command = plan

  module {
    source = "./"
  }

  variables {
    name          = "tf-test-scale-down-disabled"
    project_id    = var.project_id
    provider_name = "AWS"
    regions = [
      {
        name       = "US_EAST_1",
        node_count = 3
      }
    ]
    cluster_type = "REPLICASET"
    # Enable auto-scaling but disable scale down
    auto_scaling = {
      compute_enabled            = true
      compute_max_instance_size  = "M50"
      compute_min_instance_size  = "M10"
      compute_scale_down_enabled = false
      disk_gb_enabled            = true
    }
  }

  # When scale_down_enabled = false, compute_min_instance_size should not be set in the plan
  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].auto_scaling.compute_scale_down_enabled == false
    error_message = "Expected compute_scale_down_enabled to be false"
  }

  # The effective auto scaling should not include compute_min_instance_size when scale_down is disabled, the value will be marked as unknown
  # Unfortunately we cannot test that, we get an error message: 
  # `Condition expression could not be evaluated at this time. This means you have executed a `run` block with `command = plan` and one of the values your condition depended on is not known until after the plan has been applied`
  # assert {
  #   condition     = !known(mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].auto_scaling.compute_min_instance_size)
  #   error_message = "Expected compute_min_instance_size to not be set when compute_scale_down_enabled = false"
  # }
  # Verify other auto-scaling settings are still applied
  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].auto_scaling.compute_enabled == true
    error_message = "Expected compute_enabled to be true"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].auto_scaling.compute_max_instance_size == "M50"
    error_message = "Expected compute_max_instance_size to be M50"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].auto_scaling.disk_gb_enabled == true
    error_message = "Expected disk_gb_enabled to be true"
  }
}

run "scale_down_enabled_should_set_compute_min_instance_size" {
  command = plan

  module {
    source = "./"
  }

  variables {
    name          = "tf-test-scale-down-enabled"
    project_id    = var.project_id
    provider_name = "AWS"
    regions = [
      {
        name       = "US_EAST_1",
        node_count = 3
      }
    ]
    cluster_type = "REPLICASET"
    # Enable auto-scaling with scale down enabled
    auto_scaling = {
      compute_enabled            = true
      compute_max_instance_size  = "M50"
      compute_min_instance_size  = "M10"
      compute_scale_down_enabled = true
      disk_gb_enabled            = true
    }
  }

  # When scale_down_enabled = true, compute_min_instance_size should be set in the plan
  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].auto_scaling.compute_scale_down_enabled == true
    error_message = "Expected compute_scale_down_enabled to be true"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].auto_scaling.compute_min_instance_size == "M10"
    error_message = "Expected compute_min_instance_size to be M10 when compute_scale_down_enabled = true"
  }
}

run "analytics_scale_down_disabled_should_not_set_compute_min_instance_size" {
  command = plan

  module {
    source = "./"
  }

  variables {
    name          = "tf-test-analytics-scale-down-disabled"
    project_id    = var.project_id
    cluster_type  = "SHARDED"
    provider_name = "AWS"
    regions = [
      {
        name                 = "US_EAST_1"
        node_count           = 3
        shard_number         = 1
        node_count_analytics = 1
      }
    ]
    # Enable auto-scaling for electable nodes
    auto_scaling = {
      compute_enabled            = true
      compute_max_instance_size  = "M50"
      compute_min_instance_size  = "M10"
      compute_scale_down_enabled = true
      disk_gb_enabled            = true
    }
    # Enable analytics auto-scaling but disable scale down
    auto_scaling_analytics = {
      compute_enabled            = true
      compute_max_instance_size  = "M50"
      compute_min_instance_size  = "M10"
      compute_scale_down_enabled = false
    }
  }

  # When scale_down_enabled = false for analytics, compute_scale_down_enabled should be false
  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].analytics_auto_scaling.compute_scale_down_enabled == false
    error_message = "Expected analytics compute_scale_down_enabled to be false"
  }

  # Verify other analytics auto-scaling settings are still applied
  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].analytics_auto_scaling.compute_enabled == true
    error_message = "Expected analytics compute_enabled to be true"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].analytics_auto_scaling.compute_max_instance_size == "M50"
    error_message = "Expected analytics compute_max_instance_size to be M50"
  }
}

run "analytics_scale_down_enabled_should_set_compute_min_instance_size" {
  command = plan

  module {
    source = "./"
  }

  variables {
    name          = "tf-test-analytics-scale-down-enabled"
    project_id    = var.project_id
    cluster_type  = "SHARDED"
    provider_name = "AWS"
    regions = [
      {
        name                 = "US_EAST_1"
        node_count           = 3
        shard_number         = 1
        node_count_analytics = 1
      }
    ]
    # Enable auto-scaling for electable nodes
    auto_scaling = {
      compute_enabled            = true
      compute_max_instance_size  = "M50"
      compute_min_instance_size  = "M10"
      compute_scale_down_enabled = true
      disk_gb_enabled            = true
    }
    # Enable analytics auto-scaling with scale down enabled
    auto_scaling_analytics = {
      compute_enabled            = true
      compute_max_instance_size  = "M50"
      compute_min_instance_size  = "M10"
      compute_scale_down_enabled = true
    }
  }

  # When scale_down_enabled = true for analytics, compute_min_instance_size should be set
  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].analytics_auto_scaling.compute_scale_down_enabled == true
    error_message = "Expected analytics compute_scale_down_enabled to be true"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].analytics_auto_scaling.compute_min_instance_size == "M10"
    error_message = "Expected analytics compute_min_instance_size to be M10 when compute_scale_down_enabled = true"
  }
}

run "analytics_auto_scaling_undefined_inherits_from_electable" {
  command = plan

  module {
    source = "./"
  }

  variables {
    name          = "tf-test-analytics-inherit"
    project_id    = var.project_id
    cluster_type  = "SHARDED"
    provider_name = "AWS"
    regions = [
      {
        name                 = "US_EAST_1"
        node_count           = 3
        shard_number         = 1
        node_count_analytics = 1
      }
    ]
    # Enable auto-scaling for electable nodes
    auto_scaling = {
      compute_enabled            = true
      compute_max_instance_size  = "M50"
      compute_min_instance_size  = "M30"
      compute_scale_down_enabled = true
      disk_gb_enabled            = true
    }
    # Do not set auto_scaling_analytics or instance_size_analytics
    # This should inherit the auto_scaling settings from electable nodes
  }

  # Analytics should inherit auto-scaling settings from electable nodes
  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].analytics_auto_scaling.compute_enabled == true
    error_message = "Expected analytics compute_enabled to inherit from electable (true)"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].analytics_auto_scaling.compute_min_instance_size == "M30"
    error_message = "Expected analytics compute_min_instance_size to inherit from electable (M30)"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].analytics_auto_scaling.compute_max_instance_size == "M50"
    error_message = "Expected analytics compute_max_instance_size to inherit from electable (M50)"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].analytics_auto_scaling.compute_scale_down_enabled == true
    error_message = "Expected analytics compute_scale_down_enabled to inherit from electable (true)"
  }
}
