module "cluster" {
  source = "../.."

  name         = "single-region"
  project_id   = var.project_id
  cluster_type = "REPLICASET"
  regions = [
    {
      name          = "US_EAST_1"
      node_count    = 3
      provider_name = "AWS"
    }
  ]
  tags = var.tags
}

output "cluster" {
  value = module.cluster
}
