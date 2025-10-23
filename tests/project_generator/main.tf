terraform {
  required_providers {
    mongodbatlas = {
      source = "mongodb/mongodbatlas"
      version = "~> 2.1.0"
    }
  }
}

provider "mongodbatlas" {
  client_id = var.client_id
  client_secret = var.client_secret
  base_url      = var.base_url
}


variable "org_id" { type = string }
variable "project_name" { type = string }
variable "client_id" { type = string }
variable "client_secret" { type = string }
variable "base_url" { type = string }

resource "mongodbatlas_project" "project_test" {
  org_id = var.org_id
  name   =  var.project_name
}

output "project_id" {
  value = mongodbatlas_project.project_test.id
}