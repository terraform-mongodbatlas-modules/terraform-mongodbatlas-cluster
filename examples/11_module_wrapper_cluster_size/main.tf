module "cluster_small" {
  source = "./modules/cluster_wrapper"

  cluster_size = "small"
  name         = "small"
  cluster_type = "REPLICASET"
  tags         = var.tags
  project_id   = var.project_id
}

output "cluster_small" {
  value = module.cluster_small
}

module "cluster_medium_sharded" {
  source = "./modules/cluster_wrapper"

  cluster_size = "medium"
  shard_count  = 3

  tags         = var.tags
  name         = "medium-sharded"
  cluster_type = "SHARDED"
  project_id   = var.project_id
}

output "cluster_medium_sharded" {
  value = module.cluster_medium_sharded
}


module "cluster_geosharded" {
  source = "./modules/cluster_wrapper"

  zones = {
    EU = {
      regions = [{
        name       = "EU_WEST_1"
        node_count = 3
      }]
      shard_count = 2
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
      shard_count = 1
    }
  }

  tags         = var.tags
  name         = "geosharded"
  cluster_type = "GEOSHARDED"
  project_id   = var.project_id
}

output "cluster_geosharded" {
  value = module.cluster_geosharded
}
