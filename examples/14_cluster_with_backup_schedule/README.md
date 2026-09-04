<!-- @generated
WARNING: This file is auto-generated. Do not edit directly.
Changes will be overwritten when documentation is regenerated.
Run 'just gen-examples' to regenerate.
-->
# Cluster with Scheduled Backups (retention override, cross-region copy, skip destroy on delete)

## Pre Requirements

If you are familiar with Terraform and already have a project configured in MongoDB Atlas go to [commands](#commands).

To use MongoDB Atlas through Terraform, ensure you meet the following requirements:

1. Install [Terraform](https://developer.hashicorp.com/terraform/install) to be able to run the `terraform` commands.
2. Sign up for a [MongoDB Atlas Account](https://www.mongodb.com/products/integrations/hashicorp-terraform)
3. Configure [authentication](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs#authentication)
4. An existing [MongoDB Atlas Project](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs/resources/project) or [optionally create a new Atlas Project resource](#optionally-create-a-new-atlas-project-resource).

## Commands

```sh
terraform init # this will download the required providers and create a `terraform.lock.hcl` file.
# configure authentication env-vars (MONGODB_ATLAS_XXX)
# configure your `vars.tfvars` with `project_id={PROJECT_ID}`
# if your cluster will be used in production, please read the "Production Considerations" below
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
module "cluster" {
  source  = "terraform-mongodbatlas-modules/cluster/mongodbatlas"
  version = "v0.4.1"

  name         = "cluster-with-backup"
  project_id   = var.project_id
  cluster_type = "SHARDED"
  regions = [
    {
      name          = "US_EAST_1"
      node_count    = 3
      provider_name = "AWS"
      shard_name    = "s1"
    },
    {
      # Auto-derived copy target (see backup_copy_region below).
      name          = "US_WEST_2"
      node_count    = 2
      provider_name = "AWS"
      shard_name    = "s1"
    }
  ]

  # backup_enabled defaults to true.
  backup_mode = "SCHEDULED" # module-managed policies. Other options: ON_DEMAND (manual snapshots only), UNMANAGED (customer-managed schedule).

  # Keep daily snapshots for 30 days instead of the 7-day default.
  backup_retention = {
    daily = { retention_value = 30 }
  }

  # Omitting `region` auto-derives the secondary from `regions` above (US_WEST_2). To pin an explicit
  # target instead: backup_copy_region = { region = "EU_WEST_1" }
  backup_copy_region = {}

  # Set to true when a Backup Compliance Policy is enabled on the project.
  backup_schedule_skip_destroy = true

  tags = var.tags
}

output "cluster" {
  value = module.cluster
}
```

**Additional files needed:**
- [variables.tf](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.4.1/examples/14_cluster_with_backup_schedule/variables.tf)
- [versions.tf](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.4.1/examples/14_cluster_with_backup_schedule/versions.tf)


## Production Considerations
- This example enables recommended production settings by default, see the [Production Recommendations (Enabled By Default)](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.4.1/README.md#production-recommendations-enabled-by-default) for details.
- However, some recommendations must be manually set, see the [Production Recommendations (Manually Configured)](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.4.1/README.md#production-recommendations-manually-configured) list.

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

- You can use this and replace the `var.project_id` with `mongodbatlas_project.this.project_id` in the [main.tf](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.4.1/examples/14_cluster_with_backup_schedule/main.tf) file.
