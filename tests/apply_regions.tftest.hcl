variables {
  org_id = "dummy"
}
run "generate_random_name" {
  module {
    source = "./tests/random_name_generator"
  }
}

run "create_project" {
  module {
    source = "./tests/project_generator"
  }

  variables {
    org_id       = var.org_id
    project_name = "test-cluster-module-tf-${run.generate_random_name.name_project}"
  }
}

run "dev_cluster" {
  command = apply

  module { source = "./." }

  variables {
    name         = "tf-test-dev-cluster"
    project_id   = run.create_project.project_id
    cluster_type = "REPLICASET"
    regions = [
      {
        name          = "US_EAST_1",
        node_count    = 3
        instance_size = "M10"
      }
    ]
    auto_scaling = {
      compute_enabled = false
    }
    retain_backups_enabled = false
    backup_enabled         = false
    pit_enabled            = false
    provider_name          = "AWS"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.cluster_type == "REPLICASET"
    error_message = "cluster_type should be REPLICASET"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].electable_specs.instance_size == "M10"
    error_message = "instance_size should be M10"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].region_configs[0].auto_scaling.compute_enabled == false
    error_message = "auto_scaling.compute_enabled should be false"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.retain_backups_enabled == false
    error_message = "retain_backups_enabled should be false"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.backup_enabled == false
    error_message = "backup_enabled should be false"
  }
}
