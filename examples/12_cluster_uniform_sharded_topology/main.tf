module "cluster" {
  source = "../.."

  name         = "multi-shard-uniform-topology"
  project_id   = var.project_id
  cluster_type = "SHARDED"

  shard_count = 3
  regions = [
    { name = "US_EAST_1", node_count = 3 },
    { name = "US_WEST_2", node_count = 2 },
  ]
  provider_name = "AWS"
  tags          = var.tags
}

output "cluster" {
  value = module.cluster
}
