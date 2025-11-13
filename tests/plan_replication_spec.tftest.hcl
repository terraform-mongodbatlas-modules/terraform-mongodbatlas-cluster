mock_provider "mongodbatlas" {}

variables {
  project_id = "000000000000000000000000"
  base_replication_specs = [{
    region_configs = [{
      provider_name = "AWS"
      region_name   = "US_EAST_1"
      priority      = 7
      electable_specs = {
        instance_size = "M10"
        node_count    = 3
      }
    }]
  }]
}

run "replication_specs_with_auto_scaling_enabled_fails" {
  command = plan
  module { source = "./" }
  variables {
    name         = "tf-test-replication-specs"
    project_id   = var.project_id
    cluster_type = "REPLICASET"
    regions      = []
    replication_specs = [{
      region_configs = [{
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
      }]
    }]
  }
  expect_failures = [var.replication_specs]
}

run "replication_specs_with_analytics_auto_scaling_enabled_fails" {
  command = plan
  module { source = "./" }
  variables {
    name         = "tf-test-replication-specs-analytics"
    project_id   = var.project_id
    cluster_type = "REPLICASET"
    regions      = []
    replication_specs = [{
      region_configs = [{
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
      }]
    }]
  }
  expect_failures = [var.replication_specs]
}

run "replication_specs_with_auto_scaling_disabled_succeeds" {
  command = plan
  module { source = "./" }
  variables {
    name         = "tf-test-replication-specs-disabled"
    project_id   = var.project_id
    cluster_type = "REPLICASET"
    regions      = []
    replication_specs = [{
      region_configs = [{
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
      }]
    }]
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
  module { source = "./" }
  variables {
    name         = "tf-test-replication-specs-no-autoscaling"
    project_id   = var.project_id
    cluster_type = "REPLICASET"
    regions      = []
    replication_specs = [{
      region_configs = [{
        provider_name = "AWS"
        region_name   = "US_EAST_1"
        priority      = 7
        electable_specs = {
          instance_size = "M10"
          node_count    = 3
        }
      }]
    }]
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

# Tests for regions-only variables used with replication_specs
# Each test sets one conflicting variable and expects validation failure

run "replication_specs_with_module_auto_scaling_modified_fails" {
  command = plan
  module { source = "./" }
  variables {
    name              = "tf-test-replication-specs-module-autoscaling"
    project_id        = var.project_id
    cluster_type      = "REPLICASET"
    regions           = []
    auto_scaling      = { compute_enabled = false, compute_max_instance_size = "M200", compute_min_instance_size = "M10", compute_scale_down_enabled = true, disk_gb_enabled = true }
    replication_specs = var.base_replication_specs
  }
  expect_failures = [var.replication_specs]
}

run "replication_specs_with_module_auto_scaling_default_succeeds" {
  command = plan
  module { source = "./" }
  variables {
    name              = "tf-test-replication-specs-module-autoscaling-default"
    project_id        = var.project_id
    cluster_type      = "REPLICASET"
    regions           = []
    replication_specs = var.base_replication_specs
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

run "replication_specs_with_auto_scaling_analytics_fails" {
  command = plan
  module { source = "./" }
  variables {
    name                   = "tf-test-replication-specs-autoscaling-analytics"
    project_id             = var.project_id
    cluster_type           = "REPLICASET"
    regions                = []
    auto_scaling_analytics = { compute_enabled = true }
    replication_specs      = var.base_replication_specs
  }
  expect_failures = [var.replication_specs]
}

run "replication_specs_with_instance_size_fails" {
  command = plan
  module { source = "./" }
  variables {
    name              = "tf-test-replication-specs-instance-size"
    project_id        = var.project_id
    cluster_type      = "REPLICASET"
    regions           = []
    instance_size     = "M30"
    replication_specs = var.base_replication_specs
  }
  expect_failures = [var.replication_specs]
}

run "replication_specs_with_instance_size_analytics_fails" {
  command = plan
  module { source = "./" }
  variables {
    name                    = "tf-test-replication-specs-instance-size-analytics"
    project_id              = var.project_id
    cluster_type            = "REPLICASET"
    regions                 = []
    instance_size_analytics = "M30"
    replication_specs       = [{ region_configs = [{ provider_name = "AWS", region_name = "US_EAST_1", priority = 7, electable_specs = { instance_size = "M10", node_count = 3 } }] }]
  }
  expect_failures = [var.replication_specs]
}

run "replication_specs_with_disk_iops_fails" {
  command = plan
  module { source = "./" }
  variables {
    name              = "tf-test-replication-specs-disk-iops"
    project_id        = var.project_id
    cluster_type      = "REPLICASET"
    regions           = []
    disk_iops         = 3000
    replication_specs = var.base_replication_specs
  }
  expect_failures = [var.replication_specs]
}

run "replication_specs_with_disk_size_gb_fails" {
  command = plan
  module { source = "./" }
  variables {
    name              = "tf-test-replication-specs-disk-size"
    project_id        = var.project_id
    cluster_type      = "REPLICASET"
    regions           = []
    disk_size_gb      = 100
    replication_specs = var.base_replication_specs
  }
  expect_failures = [var.replication_specs]
}

run "replication_specs_with_ebs_volume_type_fails" {
  command = plan
  module { source = "./" }
  variables {
    name              = "tf-test-replication-specs-ebs-volume"
    project_id        = var.project_id
    cluster_type      = "REPLICASET"
    regions           = []
    ebs_volume_type   = "PROVISIONED"
    replication_specs = var.base_replication_specs
  }
  expect_failures = [var.replication_specs]
}

run "replication_specs_with_shard_count_fails" {
  command = plan
  module { source = "./" }
  variables {
    name              = "tf-test-replication-specs-shard-count"
    project_id        = var.project_id
    cluster_type      = "SHARDED"
    regions           = []
    shard_count       = 2
    replication_specs = var.base_replication_specs
  }
  expect_failures = [var.replication_specs]
}

run "replication_specs_with_provider_name_fails" {
  command = plan
  module { source = "./" }
  variables {
    name              = "tf-test-replication-specs-provider-name"
    project_id        = var.project_id
    cluster_type      = "REPLICASET"
    regions           = []
    provider_name     = "AWS"
    replication_specs = var.base_replication_specs
  }
  expect_failures = [var.replication_specs]
}
