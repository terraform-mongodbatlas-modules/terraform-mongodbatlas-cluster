module "cluster" {
  source = "../.."

  name         = "single-region"
  project_id   = var.project_id
  cluster_type = "SHARDED"
  regions = [
    {
      name          = "US_EAST_1"
      node_count    = 3
      provider_name = "AWS"
      shard_number  = 1
    }
  ]
  tags = var.tags
}

output "cluster" {
  value = module.cluster
}
