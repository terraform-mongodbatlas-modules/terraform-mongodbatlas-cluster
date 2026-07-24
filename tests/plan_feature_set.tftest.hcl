mock_provider "mongodbatlas" {}

variables {
  project_id    = "000000000000000000000000"
  name          = "tf-test-feature-set"
  provider_name = "AWS"
  cluster_type  = "REPLICASET"
  regions       = [{ name = "US_EAST_1", node_count = 3 }]
}

run "invalid_feature_set" {
  command         = plan
  expect_failures = [var.default_feature_set]
  module { source = "./" }

  variables {
    default_feature_set = "EXPERIMENTAL"
  }
}

run "recommended_defaults_to_tls1_3" {
  command = plan
  module { source = "./" }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.advanced_configuration.minimum_enabled_tls_protocol == "TLS1_3"
    error_message = "RECOMMENDED should set minimum_enabled_tls_protocol to TLS1_3"
  }
}

run "explicit_tls1_2_wins_under_recommended" {
  command = plan
  module { source = "./" }

  variables {
    advanced_configuration = {
      minimum_enabled_tls_protocol = "TLS1_2"
    }
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.advanced_configuration.minimum_enabled_tls_protocol == "TLS1_2"
    error_message = "Explicit TLS1_2 must win under RECOMMENDED"
  }
}

run "explicit_tls1_3_wins_under_standard" {
  command = plan
  module { source = "./" }

  variables {
    default_feature_set = "STANDARD"
    advanced_configuration = {
      minimum_enabled_tls_protocol = "TLS1_3"
    }
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.advanced_configuration.minimum_enabled_tls_protocol == "TLS1_3"
    error_message = "Explicit TLS1_3 must win under STANDARD"
  }
}
