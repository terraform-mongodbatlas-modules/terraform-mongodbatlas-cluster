# Example: Import a cluster by name
# The module will fetch the cluster data and generate one .tf file per cluster

terraform {
  required_version = ">= 1.6"
  required_providers {
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "~> 2.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "2.4.1"
    }
  }
}

provider "mongodbatlas" {}

variable "project_id" {
  description = "MongoDB Atlas Project ID"
  type        = string
}

data "mongodbatlas_advanced_clusters" "this" {
  project_id = var.project_id
}

module "cluster_import" {
  source = "../../modules/cluster_import"

  for_each = {
    for cluster in data.mongodbatlas_advanced_clusters.this.results : cluster.name => cluster
  }

  cluster_name     = each.key
  project_id       = var.project_id
  output_directory = "${path.module}/clusters"
}

output "summaries" {
  description = "Summary of the imported clusters"
  value = {
    for cluster in module.cluster_import : cluster.name => cluster.summary
  }
}

output "filepaths" {
  description = "Filepath of the imported clusters"
  value = {
    for cluster in module.cluster_import : cluster.name => cluster.filepath
  }

}
