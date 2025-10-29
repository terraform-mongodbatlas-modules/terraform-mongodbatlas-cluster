data "mongodbatlas_advanced_clusters" "this" {
  project_id = var.project_id
}

data "mongodbatlas_advanced_cluster" "this" {
  project_id = var.project_id
  name       = var.name
}

locals {
  existing_cluster = try(element([for cluster in data.mongodbatlas_advanced_clusters.this.results : { old_cluster = cluster } if cluster.name == var.name], 0), tomap({}))
}
