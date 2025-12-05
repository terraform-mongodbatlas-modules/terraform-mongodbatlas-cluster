terraform {
  required_providers {
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "~> 2.1"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
  required_version = ">= 1.9"
}

variable "project_id" {
  type        = string
  default     = null
  description = "Project ID. If not set, creates a new project via project_generator."
}

variable "project_name" {
  type        = string
  default     = "ws-cluster-examples-test"
  description = "Project name when creating via project_generator."
}

module "proj" {
  count        = var.project_id == null ? 1 : 0
  source       = "../project_generator"
  org_id       = var.org_id
  project_name = var.project_name
}

locals {
  project_id = var.project_id != null ? var.project_id : module.proj[0].project_id
}

# Example 01: Production cluster with auto scaling
module "ex_01" {
  source     = "../../examples/01_production_cluster_with_auto_scaling"
  project_id = local.project_id
  tags       = {}
}

# Example 08: Development cluster
module "ex_08" {
  source     = "../../examples/08_development_cluster"
  project_id = local.project_id
  tags       = {}
}
