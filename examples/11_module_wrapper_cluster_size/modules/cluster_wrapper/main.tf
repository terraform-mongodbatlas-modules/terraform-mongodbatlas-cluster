locals {
  # P = primary
  # S = secondary
  # - new region

  # PSS - Single region
  small = [
    {
      name       = var.regions_names[0]
      node_count = 3
    }
  ]
  # PS-SS-S - 3 region 2 nodes, allows region failure
  medium = [
    {
      name       = var.regions_names[0]
      node_count = 2
    },
    {
      name       = var.regions_names[1]
      node_count = 2
    },
    {
      name       = var.regions_names[2]
      node_count = 1
    },
  ]
  # PSS-SSS-S 3 regions 3 nodes in each, allows region failure
  large = [
    {
      name       = var.regions_names[0]
      node_count = 3
    },
    {
      name       = var.regions_names[1]
      node_count = 3
    },
    {
      name       = var.regions_names[2]
      node_count = 1
    },
  ]
  sizes = {
    small  = local.small
    medium = local.medium
    large  = local.large
  }

  regions = [for region in lookup(local.sizes, var.cluster_size, []) : merge(region, var.region_extra)]
  regions_zones = flatten(
    [for zone_name, zone_config in var.zones :
      flatten([for shard in range(zone_config.shard_count) :
        [for region_config in zone_config.regions :
          merge({
            zone_name    = zone_name
            shard_number = shard
        }, region_config)]
      ])
    ]
  )
  final_regions = length(local.regions) > 0 ? local.regions : local.regions_zones
}


module "cluster" {
  source = "../../../.."

  name         = var.name
  project_id   = var.project_id
  cluster_type = var.cluster_type

  regions       = local.final_regions
  shard_count   = var.shard_count
  provider_name = "AWS" # Opinionated company default provider
  tags          = var.tags
}
