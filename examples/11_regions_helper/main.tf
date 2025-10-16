module "regions_replicaset_small" {
  source = "./modules/regions_helper"

  cluster_size = "small"
}

module "cluster_small" {
  source = "../.."

  tags          = var.tags
  regions       = module.regions_replicaset_small.regions
  name          = "small"
  provider_name = "AWS"
  cluster_type  = "REPLICASET"
  project_id    = var.project_id
}

output "cluster_small" {
  value = module.cluster_small
}

module "regions_sharded_medium" {
  source = "./modules/regions_helper"

  cluster_size = "medium"
  shards       = 3
}

output "regions_cluster_medium_sharded" {
  value = module.regions_sharded_medium.regions
}

module "cluster_medium_sharded" {
  source = "../.."

  tags          = var.tags
  regions       = module.regions_sharded_medium.regions
  name          = "medium-sharded"
  provider_name = "AWS"
  cluster_type  = "SHARDED"
  project_id    = var.project_id
}

output "cluster_medium_sharded" {
  value = module.cluster_medium_sharded
}

module "regions_cluster_geosharded" {
  source = "./modules/regions_helper"

  zones = {
    EU = {
      regions = [{
        name       = "EU_WEST_1"
        node_count = 3
      }]
      shards = 2
    }
    US = {
      regions = [{
        name                 = "US_EAST_1"
        node_count           = 3
        node_count_read_only = 2
        }, {
        name       = "US_EAST_2"
        node_count = 2
        }
      ]
      shards = 1
    }
  }

}

output "regions_geosharded" {
  value = module.regions_cluster_geosharded
}

module "cluster_geosharded" {
  source = "../.."

  tags          = var.tags
  regions       = module.regions_cluster_geosharded.regions
  name          = "geosharded"
  cluster_type  = "GEOSHARDED"
  provider_name = "AWS"
  project_id    = var.project_id
}

output "cluster_geosharded" {
  value = module.cluster_geosharded
}
