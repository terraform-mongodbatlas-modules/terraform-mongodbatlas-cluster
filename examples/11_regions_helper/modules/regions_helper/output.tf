output "regions" {
  value = coalescelist(local.regions_sharded, local.regions, local.regions_zones)
}
