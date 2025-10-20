module "replication_var" {
  source = "../.."

  name                   = "replication-var"
  project_id             = var.project_id
  mongo_db_major_version = "8.0"
  regions                = []
  cluster_type           = "SHARDED"
  replication_specs = [{
    region_configs = [{
      priority      = 7
      provider_name = "AWS"
      region_name   = "US_EAST_1"
      shard_number  = 1
      electable_specs = {
        instance_size = "M10"
        node_count    = 3
      }
    }]
  }]
  tags = var.tags
}
