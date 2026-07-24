mock_provider "mongodbatlas" {}

variables {
  project_id     = "000000000000000000000000"
  name           = "tf-test-version"
  provider_name  = "AWS"
  cluster_type   = "REPLICASET"
  instance_size  = "M10"
  backup_enabled = false
  auto_scaling   = { compute_enabled = false }
  regions        = [{ name = "US_EAST_1", node_count = 3 }]
}

run "continuous_with_major_version_fails" {
  command         = plan
  expect_failures = [var.version_release_system]
  module { source = "./" }

  variables {
    version_release_system = "CONTINUOUS"
    mongo_db_major_version = "8.0"
  }
}

run "continuous_alone_succeeds" {
  command = plan
  module { source = "./" }

  variables {
    version_release_system = "CONTINUOUS"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.version_release_system == "CONTINUOUS"
    error_message = "version_release_system should pass through as CONTINUOUS"
  }
}

run "lts_with_major_version_succeeds" {
  command = plan
  module { source = "./" }

  variables {
    version_release_system = "LTS"
    mongo_db_major_version = "8.0"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.mongo_db_major_version == "8.0"
    error_message = "LTS with mongo_db_major_version should be allowed"
  }
}

run "major_version_alone_succeeds" {
  command = plan
  module { source = "./" }

  variables {
    mongo_db_major_version = "8.0"
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.mongo_db_major_version == "8.0"
    error_message = "mongo_db_major_version alone should be allowed"
  }
}
