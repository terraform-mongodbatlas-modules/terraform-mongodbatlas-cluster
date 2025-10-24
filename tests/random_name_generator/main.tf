terraform {
  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "3.6.2"
    }
  }
}

resource "random_string" "name_project" {
  keepers = {
    first = "${timestamp()}"
  }
  length  = 16
  special = false
  numeric = false
}

output "name_project" {
  value = random_string.name_project.id
}