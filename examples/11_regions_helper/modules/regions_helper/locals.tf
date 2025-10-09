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
}
