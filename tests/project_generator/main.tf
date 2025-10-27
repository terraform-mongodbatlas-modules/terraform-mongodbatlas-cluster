terraform {
  required_providers {
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "~> 2.1"
    }
  }
  required_version = ">= 1.6"
}

variable "org_id" { type = string }
variable "project_name" { type = string }

resource "mongodbatlas_project" "project_test" {
  org_id = var.org_id
  name   = var.project_name
}

output "project_id" {
  value = mongodbatlas_project.project_test.id
}