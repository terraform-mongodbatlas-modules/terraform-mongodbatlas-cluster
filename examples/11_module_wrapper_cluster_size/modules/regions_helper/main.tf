locals {
  regions = [for region in lookup(local.sizes, var.cluster_size, []) : merge(region, var.region_extra)]
  regions_sharded = flatten(
    [for shard in range(var.shards) :
      [for region in local.regions : merge(region, { shard_number = shard })]
    ]
  )
  regions_zones = flatten(
    [for zone_name, zone_config in var.zones :
      flatten([for shard in range(zone_config.shards) :
        [for region_config in zone_config.regions :
          merge({
            zone_name    = zone_name
            shard_number = shard
        }, region_config)]
      ])
    ]
  )
}
