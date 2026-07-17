
terraform {
  required_providers {
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "~> 2.1"
    }
  }
  required_version = ">= 1.10"

  # These values are used in the User-Agent Header
  provider_meta "mongodbatlas" {
    module_name    = "cluster"
    module_version = "local"
  }
}
