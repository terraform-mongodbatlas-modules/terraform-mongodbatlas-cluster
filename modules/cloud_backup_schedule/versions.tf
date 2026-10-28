terraform {
  required_version = ">= 1.10"
  required_providers {
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "~> 2.18"
    }
  }

  provider_meta "mongodbatlas" {
    module_name    = "cluster/cloud_backup_schedule"
    module_version = "1.0.0"
  }
}
