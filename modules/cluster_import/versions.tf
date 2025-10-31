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
