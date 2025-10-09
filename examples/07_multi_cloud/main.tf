module "cluster" {
  source = "../.."

  name         = "multi-cloud"
  project_id   = var.project_id
  cluster_type = "SHARDED"
  regions = [
    {
      name                 = "US_WEST_2"
      node_count           = 2
      shard_number         = 0
      node_count_read_only = 2
      provider_name        = "AZURE"
      }, {
      name                 = "US_EAST_2"
      node_count           = 1
      shard_number         = 0
      provider_name        = "AWS"
      node_count_read_only = 2
    },
    {
      name                 = "US_WEST_2"
      node_count           = 2
      shard_number         = 1
      node_count_read_only = 2
      provider_name        = "AZURE"
      }, {
      name                 = "US_EAST_2"
      node_count           = 1
      shard_number         = 1
      provider_name        = "AWS"
      node_count_read_only = 2
    }
  ]
  tags = var.tags
}

output "cluster" {
  value = module.cluster
}
