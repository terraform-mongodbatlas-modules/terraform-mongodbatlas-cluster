variable "cluster_name" {
  type        = string
  default     = ""
  description = "Name of the cluster. Leave empty for a valid generated name."
}

variable "name_prefix" {
  description = "Prefix for the cluster name if not specified in the `name` variable."
  type        = string
  default     = "lz-module-"
}


resource "random_pet" "generated_name" {
  prefix = trim(var.name_prefix, "-")
  length = 2
  keepers = {
    prefix = var.name_prefix
  }
}

# POST: HTTP 400 Bad Request (Error code: "CLUSTER_NAME_PREFIX_INVALID") Detail: Cluster name "more-than-twenty-three-check-long-name-very-long-even--chars" is invalid.
# Atlas truncates cluster names to 23 characters which results in an invalid hostname due to a trailing "-" in the generated cluster name 
module "cluster" {
  source = "../.." # "terraform-mongodbatlas-modules/cluster/mongodbatlas"

  # Disable default production values
  auto_scaling = {
    compute_enabled = false # use manual instance_size to avoid any accidental cost
  }
  retain_backups_enabled = false # don't keep backups when deleting the cluster
  backup_enabled         = false # skip backup for dev cluster
  pit_enabled            = false # skip pit_backup for dev cluster

  cluster_type = "REPLICASET"
  name         = coalesce(var.cluster_name, substr(trim(random_pet.generated_name.id, "-"), 0, 23))
  project_id   = var.project_id
  regions = [
    {
      name          = "US_EAST_1" # https://www.mongodb.com/docs/atlas/cloud-providers-regions/
      node_count    = 3           # Minimum node count. Most be an odd number to support elections.
      instance_size = "M10"       # 2vCPUs and 2GB Ram
    }
  ]
  provider_name = "AWS"
  tags          = var.tags
}

output "cluster" {
  value = module.cluster
}
