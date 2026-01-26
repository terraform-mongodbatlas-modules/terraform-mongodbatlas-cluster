mock_provider "mongodbatlas" {}

variables {
  project_id = "000000000000000000000000"
}

run "backup_true_pit_null_defaults_to_true" {
  command = plan
  module { source = "./" }

  variables {
    name          = "tf-test-backup-pit"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "REPLICASET"
    regions       = [{ name = "US_EAST_1", node_count = 3 }]
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.pit_enabled == true
    error_message = "pit_enabled should default to true when backup_enabled=true"
  }
}

run "backup_false_pit_null_auto_disables" {
  command = plan
  module { source = "./" }

  variables {
    name           = "tf-test-backup-disabled"
    project_id     = var.project_id
    provider_name  = "AWS"
    cluster_type   = "REPLICASET"
    instance_size  = "M10"
    backup_enabled = false
    auto_scaling   = { compute_enabled = false }
    regions        = [{ name = "US_EAST_1", node_count = 3 }]
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.pit_enabled == false
    error_message = "pit_enabled should auto-disable when backup_enabled=false and pit_enabled=null"
  }
}

run "backup_false_pit_true_validation_error" {
  command         = plan
  expect_failures = [var.pit_enabled]
  module { source = "./" }

  variables {
    name           = "tf-test-conflict"
    project_id     = var.project_id
    provider_name  = "AWS"
    cluster_type   = "REPLICASET"
    instance_size  = "M10"
    backup_enabled = false
    pit_enabled    = true
    auto_scaling   = { compute_enabled = false }
    regions        = [{ name = "US_EAST_1", node_count = 3 }]
  }
}

run "backup_true_pit_false_works" {
  command = plan
  module { source = "./" }

  variables {
    name          = "tf-test-pit-disabled"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "REPLICASET"
    pit_enabled   = false
    regions       = [{ name = "US_EAST_1", node_count = 3 }]
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.pit_enabled == false
    error_message = "pit_enabled should be false when explicitly set"
  }
}
