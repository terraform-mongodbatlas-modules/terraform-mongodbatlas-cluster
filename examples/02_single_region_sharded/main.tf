module "cluster" {
  source = "../.."

  auto_scaling = {
    compute_enabled = false
  }
  name         = "single-region-sharded"
  project_id   = var.project_id
  cluster_type = "SHARDED"
  regions = [
    {
      name          = "US_EAST_1"
      node_count    = 3
      shard_number  = 1
      instance_size = "M40"
      }, {
      name          = "US_EAST_1"
      node_count    = 3
      shard_number  = 2
      instance_size = "M30"
    }
  ]
  provider_name = "AWS"

  tags = var.tags
}

output "cluster" {
  value = module.cluster
}
