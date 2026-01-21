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

variable "org_id" {
  type        = string
  description = "Organization ID for creating the project."
}

variable "project_name" {
  type        = string
  default     = ""
  description = "Project name. If empty, generates from prefix + random suffix."
}

variable "project_name_prefix" {
  type        = string
  default     = "test-acc-tf-p-" # DO NOT EDIT, prefix used by cleanup-test-env.yml
  description = "Project name prefix when auto-generating name."
}

resource "random_string" "suffix" {
  count = var.project_name == "" ? 1 : 0
  keepers = {
    first = timestamp()
  }
  length  = 6
  special = false
  upper   = false
}

locals {
  project_name = var.project_name != "" ? var.project_name : "${var.project_name_prefix}${random_string.suffix[0].id}"
}

resource "mongodbatlas_project" "this" {
  org_id = var.org_id
  name   = local.project_name

  lifecycle {
    precondition {
      condition     = var.org_id != ""
      error_message = "org_id must be set"
    }
  }
}

output "project_id" {
  value = mongodbatlas_project.this.id
}

output "project_name" {
  value = mongodbatlas_project.this.name
}
