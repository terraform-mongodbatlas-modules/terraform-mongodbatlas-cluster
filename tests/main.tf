terraform {
  required_providers {
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "~> 2.2"
    }
  }
  required_version = ">= 1.10"
}

provider "mongodbatlas" {
  # Credentials come from env vars, using Service Accounts:
  # MONGODB_ATLAS_CLIENT_ID / MONGODB_ATLAS_CLIENT_SECRET
  # Optionally override base URL via MONGODB_ATLAS_BASE_URL
}
