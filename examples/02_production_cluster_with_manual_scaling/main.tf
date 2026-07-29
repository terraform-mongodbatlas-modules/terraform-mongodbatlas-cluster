module "cluster" {
  source = "../.."

  auto_scaling = {
    compute_enabled = false
  }
  instance_size = "M40"
  name          = "single-region-sharded"
  project_id    = var.project_id
  cluster_type  = "SHARDED"
  regions = [
    {
      name       = "US_EAST_1"
      node_count = 3
      shard_name = "s1"
      }, {
      name       = "US_EAST_1"
      node_count = 3
      shard_name = "s2"
    }
  ]
  provider_name = "AWS"

  tags = var.tags
}

output "cluster" {
  value = module.cluster
}
