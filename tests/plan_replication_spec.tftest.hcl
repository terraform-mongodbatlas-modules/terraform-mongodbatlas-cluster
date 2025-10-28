mock_provider "mongodbatlas" {}

variables {
  project_id = "000000000000000000000000"
}

run "replication_specs_with_auto_scaling_enabled_fails" {
  command = plan

  module {
    source = "./"
  }

  variables {
    name         = "tf-test-replication-specs"
    project_id   = var.project_id
    cluster_type = "REPLICASET"
    regions      = []
    replication_specs = [
      {
        region_configs = [
          {
            provider_name = "AWS"
            region_name   = "US_EAST_1"
            priority      = 7
            electable_specs = {
              instance_size = "M10"
              node_count    = 3
            }
            auto_scaling = {
              compute_enabled            = true
              compute_min_instance_size  = "M10"
              compute_max_instance_size  = "M40"
              compute_scale_down_enabled = true
              disk_gb_enabled            = true
            }
          }
        ]
      }
    ]
  }

  expect_failures = [
    var.replication_specs,
  ]
}

run "replication_specs_with_analytics_auto_scaling_enabled_fails" {
  command = plan

  module {
    source = "./"
  }

  variables {
    name         = "tf-test-replication-specs-analytics"
    project_id   = var.project_id
    cluster_type = "REPLICASET"
    regions      = []
    replication_specs = [
      {
        region_configs = [
          {
            provider_name = "AWS"
            region_name   = "US_EAST_1"
            priority      = 7
            electable_specs = {
              instance_size = "M10"
              node_count    = 3
            }
            analytics_auto_scaling = {
              compute_enabled            = true
              compute_min_instance_size  = "M10"
              compute_max_instance_size  = "M40"
              compute_scale_down_enabled = true
              disk_gb_enabled            = true
            }
          }
        ]
      }
    ]
  }

  expect_failures = [
    var.replication_specs,
  ]
}

run "replication_specs_with_auto_scaling_disabled_succeeds" {
  command = plan

  module {
    source = "./"
  }

  variables {
    name         = "tf-test-replication-specs-disabled"
    project_id   = var.project_id
    cluster_type = "REPLICASET"
    regions      = []
    replication_specs = [
      {
        region_configs = [
          {
            provider_name = "AWS"
            region_name   = "US_EAST_1"
            priority      = 7
            electable_specs = {
              instance_size = "M10"
              node_count    = 3
            }
            auto_scaling = {
              compute_enabled = false
            }
          }
        ]
      }
    ]
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.cluster_type == "REPLICASET"
    error_message = "cluster_type should be REPLICASET"
  }

  assert {
    condition     = length(mongodbatlas_advanced_cluster.this.replication_specs) == 1
    error_message = "should have exactly 1 replication spec"
  }
}

run "replication_specs_with_no_auto_scaling_succeeds" {
  command = plan

  module {
    source = "./"
  }

  variables {
    name         = "tf-test-replication-specs-no-autoscaling"
    project_id   = var.project_id
    cluster_type = "REPLICASET"
    regions      = []
    replication_specs = [
      {
        region_configs = [
          {
            provider_name = "AWS"
            region_name   = "US_EAST_1"
            priority      = 7
            electable_specs = {
              instance_size = "M10"
              node_count    = 3
            }
          }
        ]
      }
    ]
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.cluster_type == "REPLICASET"
    error_message = "cluster_type should be REPLICASET"
  }

  assert {
    condition     = length(mongodbatlas_advanced_cluster.this.replication_specs) == 1
    error_message = "should have exactly 1 replication spec"
  }
}
