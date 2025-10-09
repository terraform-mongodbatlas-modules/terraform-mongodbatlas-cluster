module "cluster" {
  source = "../.."

  name                   = "multi-geo-zone-sharded"
  project_id             = var.project_id
  mongo_db_major_version = "8.0"
  cluster_type           = "GEOSHARDED"
  regions = [
    {
      name       = "US_EAST_1"
      node_count = 3
      zone_name  = "US"
      }, {
      name       = "EU_WEST_1"
      node_count = 3
      zone_name  = "EU"
    }
  ]
  provider_name = "AWS"
  tags = var.tags
}

output "cluster" {
  value = module.cluster
}
