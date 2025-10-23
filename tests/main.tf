terraform {
  required_providers {
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "~> 2.1"
    }
  }
  required_version = ">= 1.6"
}

variable "client_id"     { type = string }
variable "client_secret" { type = string }

variable "base_url" {
  type    = string
  default = "https://cloud.mongodb.com/"
}

provider "mongodbatlas" {
  client_id     = var.client_id
  client_secret = var.client_secret
  base_url      = var.base_url
}