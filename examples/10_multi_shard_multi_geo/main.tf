module "cluster" {
  source = "../.."

  name         = "multi-zone-geo-sharded"
  project_id   = var.project_id
  cluster_type = "GEOSHARDED"
  regions = [
    {
      name         = "US_EAST_1"
      node_count   = 3
      zone_name    = "US"
      shard_number = 0
    },
    {
      name         = "US_EAST_2"
      node_count   = 2
      zone_name    = "US"
      shard_number = 0
    },
    {
      name         = "US_WEST_2"
      node_count   = 2
      zone_name    = "US"
      shard_number = 0
    },
    {
      name         = "US_EAST_1"
      node_count   = 3
      zone_name    = "US"
      shard_number = 1
    },
    {
      name         = "US_EAST_2"
      node_count   = 2
      zone_name    = "US"
      shard_number = 1
    },
    {
      name         = "US_WEST_2"
      node_count   = 2
      zone_name    = "US"
      shard_number = 1
    },
    {
      name                 = "EU_WEST_1"
      node_count           = 3
      node_count_read_only = 2
      zone_name            = "EU"
      shard_number         = 0
    },
    {
      name                 = "EU_WEST_2"
      node_count           = 3
      node_count_read_only = 2
      zone_name            = "EU2"
      shard_number         = 0
    }
  ]
  provider_name = "AWS"
  auto_scaling = {
    compute_enabled            = true
    compute_max_instance_size  = "M60"
    compute_min_instance_size  = "M30"
    compute_scale_down_enabled = true
    disk_gb_enabled            = true
  }

  tags = var.tags
}

output "cluster" {
  value = module.cluster
}
