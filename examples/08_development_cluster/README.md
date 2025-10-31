<!-- This file is used to generate the examples/README.md files -->
# Development Cluster

## Pre Requirements
If you are familiar with Terraform and already have a project configured in MongoDB Atlas go to [commands](#commands)

1. To run the `terraform` commands you need to install [Terraform](https://developer.hashicorp.com/terraform/install).
2. Sign up for a [MongoDB Atlas Account](https://www.mongodb.com/products/integrations/hashicorp-terraform)
3. Configure [authentication](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs#authentication)
4. An existing [MongoDB Atlas Project](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs/resources/project) or [optionally create a new Atlas Project resource](#optionally-create-a-new-atlas-project-resource).

## Commands
```sh
terraform init # this will download the required providers and create a `terraform.lock.hcl` file.
# configure authentication env-vars (MONGODB_ATLAS_XXX)
# configure your `vars.tfvars` with `project_id={PROJECT_ID}`

terraform apply -var-file vars.tfvars
# Find the connection string (will not include the username and password, see the [database_user](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs/resources/database_user) documentation to configure your app's access)
terraform output cluster.connection_strings
# cleanup
terraform destroy -var-file vars.tfvars
```

## Code Snippet

Copy and use this code to get started quickly:

**main.tf**
```hcl
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

module "cluster" {
  source  = "terraform-mongodbatlas-modules/cluster/mongodbatlas"
  version = "v0.1.0"

  # Disable default production values
  auto_scaling = {
    compute_enabled = false # use manual instance_size to avoid any accidental cost
  }
  retain_backups_enabled = false # don't keep backups when deleting the cluster
  backup_enabled         = false # skip backup for dev cluster
  pit_enabled            = false # skip pit_backup for dev cluster

  cluster_type = "REPLICASET"

  # Atlas truncates cluster names to 23 characters which results in an invalid hostname due to a trailing "-" in the generated cluster name 
  name       = coalesce(var.cluster_name, substr(trim(random_pet.generated_name.id, "-"), 0, 23))
  project_id = var.project_id
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
```

**Additional files needed:**
- [variables.tf](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.1.0/examples/08_development_cluster/variables.tf)
- [versions.tf](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.1.0/examples/08_development_cluster/versions.tf)




## Feedback or Help
- If you have any feedback or trouble please open a Github Issue

## Optionally Create a New Atlas Project Resource
```hcl
variable "org_id" {
  type    = string
  default = "{ORG_ID}" # REPLACE with your organization id, for example `65def6ce0f722a1507105aa5`.
}

resource "mongodbatlas_project" "this" {
  name   = "cluster-module"
  org_id = var.org_id
}
```

- You can use this and replace the `var.project_id` with `mongodbatlas_project.this.project_id` in the [main.tf](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.1.0/examples/08_development_cluster/main.tf) file.
