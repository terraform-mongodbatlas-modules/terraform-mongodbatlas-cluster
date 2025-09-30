
terraform {
  required_providers {
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "~> 2.0"
    }
  }
  required_version = ">= 1.6"

  provider_meta "mongodbatlas" {
    module_name    = "cluster"
    module_version = "0.0.1"
  }
}
