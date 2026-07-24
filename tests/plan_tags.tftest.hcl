# Verify tags defaults to null (import-clean) and passes an explicit map through.
mock_provider "mongodbatlas" {}

variables {
  project_id = "000000000000000000000000"
}

run "tags_default_null" {
  command = plan
  module { source = "./" }

  variables {
    name          = "tf-test-tags-default"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "REPLICASET"
    regions       = [{ name = "US_WEST_2", node_count = 3 }]
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.tags == null
    error_message = "tags should default to null so imported clusters without tags plan clean"
  }
}

run "tags_explicit_map" {
  command = plan
  module { source = "./" }

  variables {
    name          = "tf-test-tags-explicit"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "REPLICASET"
    regions       = [{ name = "US_WEST_2", node_count = 3 }]
    tags          = { Team = "atlas", Environment = "test" }
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.tags == tomap({ Team = "atlas", Environment = "test" })
    error_message = "explicit tags map should pass through unchanged"
  }
}
