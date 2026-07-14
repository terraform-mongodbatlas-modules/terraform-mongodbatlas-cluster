terraform {
  required_providers {
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "~> 2.1"
    }
  }
  required_version = ">= 1.9"
}

variable "project_id" {
  type        = string
  description = "Project ID owning the cluster."
}

variable "cluster_name" {
  type        = string
  description = "Cluster name whose backup schedule should be read back directly from Atlas."
}

data "mongodbatlas_cloud_backup_schedule" "this" {
  project_id   = var.project_id
  cluster_name = var.cluster_name
}

output "policy_item_daily" {
  value = data.mongodbatlas_cloud_backup_schedule.this.policy_item_daily
}
