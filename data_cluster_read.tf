data "mongodbatlas_advanced_clusters" "this" {
  project_id = var.project_id
}

locals {
  existing_cluster = try(element([for cluster in data.mongodbatlas_advanced_clusters.this.results : { old_cluster = cluster } if cluster.name == local.final_name], 0), tomap({}))
}
