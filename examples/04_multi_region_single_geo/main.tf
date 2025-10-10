module "cluster" {
  source = "../.."

  name                   = "multi-region-single-geo"
  project_id             = var.project_id
  mongo_db_major_version = "8.0"
  cluster_type           = "REPLICASET"
  regions = [
    {
      name       = "US_EAST_1"
      node_count = 2
      }, {
      name                 = "US_EAST_2"
      node_count           = 1
      node_count_read_only = 2
    }
  ]
  provider_name = "AWS"
  tags          = var.tags
}

output "cluster" {
  value = module.cluster
}
