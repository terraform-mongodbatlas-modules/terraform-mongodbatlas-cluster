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
      shard_number = 1
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
