module "cluster" {
  source = "../.."

  name         = "multi-region-multi-geo"
  project_id   = var.project_id
  cluster_type = "SHARDED"
  regions = [
    {
      name         = "US_EAST_1"
      node_count   = 3
      shard_number = 0
      }, {
      name         = "EU_WEST_1"
      node_count   = 2
      shard_number = 0
    }
  ]
  provider_name = "AWS"
  tags = var.tags
}
