run "geo_zone_initial_apply" {
  command   = apply
  state_key = "geo_zone_renaming"

  module {
    source = "../"
  }
  variables {
    name          = "tf-test-geo-zone"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "GEOSHARDED"
    regions = [
      { name = "US_EAST_1", node_count = 3, zone_name = "US" },
      { name = "EU_WEST_1", node_count = 3, zone_name = "EU" }
    ]
  }


}

run "geo_zone_rename_plan" {
  command   = plan
  state_key = "geo_zone_renaming"

  module {
    source = "../"
  }

  variables {
    name          = "tf-test-geo-zone"
    project_id    = var.project_id
    provider_name = "AWS"
    cluster_type  = "GEOSHARDED"
    regions = [
      { name = "US_EAST_1", node_count = 3, zone_name = "AMER" }, # zone renamed
      { name = "EU_WEST_1", node_count = 3, zone_name = "EU" }
    ]
  }

  assert {
    condition     = mongodbatlas_advanced_cluster.this.replication_specs[0].zone_name == "AMER"
    error_message = "Expected renamed zone to persist"
  }
}
