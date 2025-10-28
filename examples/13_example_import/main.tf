# Example: Import a cluster by name
# The module will fetch the cluster data and generate a .tf file

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

variable "cluster_name" {
  description = "Name of the cluster to import"
  type        = string
}

# Import cluster by name
module "cluster_import" {
  source = "./modules/cluster_import"

  cluster_name     = var.cluster_name
  project_id       = var.project_id
  output_directory = path.module
}
