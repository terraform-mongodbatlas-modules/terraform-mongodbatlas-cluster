
mock_provider "mongodbatlas" {
  override_during = plan
  mock_data "mongodbatlas_advanced_cluster" {
    defaults = {
      project_id             = "000000000000000000000001"
      name                   = "tf-test-autoscaling-enabled"
      cluster_type           = "REPLICASET"
      mongo_db_major_version = "999.0"
      replication_specs = {
        region_configs = {
          electable_specs = {
            instance_size = "M200"
          }
        }
      }
    }
  }
  mock_data "mongodbatlas_advanced_clusters" {
    defaults = {
      project_id = "000000000000000000000001"
      # NOTE how results and replication_specs are both a single object. This is due to the limitation of terraform test mocking:
      # https://developer.hashicorp.com/terraform/language/tests/mocking#repeated-blocks-and-nested-attributes
      # Error message if not used:
      # Terraform could not compute a value for the target type list of object with the mocked data defined at tests/plan_auto_scaling_mock_data.tftest.hcl:20,5-34,6 with the attribute ".results": incompatible types; expected object type, found tuple.
      results = {
        name         = "tf-test-autoscaling-enabled"
        project_id   = "000000000000000000000000"
        cluster_type = "REPLICASET"
        replication_specs = {
          region_configs = {
            electable_specs = {
              instance_size = "M200"
            }
          }
        }
      }
    }
  }
}


run "autoscaling_data_source_value_for_instance_size" {
  command = plan

  module {
    # source = "./tests/my-module" # using a 
    source = "./"
  }


  variables {
    name          = "tf-test-autoscaling-enabled"
    project_id    = "000000000000000000000000"
    cluster_type  = "REPLICASET"
    provider_name = "AWS"
    regions = [
      {
        name       = "US_EAST_1"
        node_count = 3
      }
    ]
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].auto_scaling.compute_min_instance_size == "M10"
    error_message = "Expected compute_min_instance_size to be M10 (from default config)"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].auto_scaling.compute_max_instance_size == "M200"
    error_message = "Expected compute_max_instance_size to be M200 (default)"
  }
  assert {
    condition     = output.cluster_count == 1
    error_message = "Expected output.cluster_count to be 1"
  }
  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].electable_specs.instance_size == "M200"
    error_message = "Expected electable_spec instance size to be M200 (from existing cluster instance_size)"
  }
}
