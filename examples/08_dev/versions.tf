
terraform {
  required_providers {
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "~> 2.0"
    }
    # used if the var.cluster_name is not provided
    random = {
      source  = "hashicorp/random"
      version = ">= 2.0"
    }
  }
  required_version = ">= 1.6"

  # These values are used in the User-Agent Header
  provider_meta "mongodbatlas" {
    module_name    = "cluster"
    module_version = "0.0.1"
  }
}

provider "mongodbatlas" {}
