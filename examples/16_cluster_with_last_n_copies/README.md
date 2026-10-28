<!-- @generated
WARNING: This file is auto-generated. Do not edit directly.
Changes will be overwritten when documentation is regenerated.
Run 'just gen-examples' to regenerate.
-->
# Cluster with Multi-Region Copy Snapshots (count-based copies, last N per region)

Copies snapshots to two secondary regions and keeps the last 5 copies in each using `backup_copy_region.region_count` and `backup_copy_region.last_number_of_snapshots`.

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
  version = "v1.0.0"

  name         = "cluster-with-last-n-copies"
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
      # Copy targets (see backup_copy_region below).
      name          = "US_WEST_2"
      node_count    = 2
      provider_name = "AWS"
      shard_name    = "s1"
    },
    {
      # Copy targets (see backup_copy_region below).
      name          = "EU_WEST_1"
      node_count    = 2
      provider_name = "AWS"
      shard_name    = "s1"
    }
  ]

  # backup_enabled defaults to true.
  backup_mode = "SCHEDULED" # module-managed policies. Other options: ON_DEMAND (manual snapshots only), UNMANAGED (customer-managed schedule).

  # Keep daily snapshots for 30 days instead of the 7-day default. Atlas requires each less frequent
  # policy item to retain at least as long as the more frequent one, so weekly is raised above the
  # default 4 weeks (28 days) to cover the 30-day daily retention.
  backup_retention = {
    daily  = { retention_value = 30 }
    weekly = { retention_value = 5 }
  }

  # Copy to the two highest-priority secondary regions (US_WEST_2 and EU_WEST_1) and keep a
  # rolling window of the last 5 copies in each. last_number_of_snapshots replaces the derived
  # copy_policy_items, so no per-frequency copy retention is sent for these targets.
  backup_copy_region = {
    region_count             = 2
    last_number_of_snapshots = 5
  }

  # Set to true when a Backup Compliance Policy is enabled on the project: Terraform removes the schedule
  # from state on destroy without deleting it in Atlas, so Atlas keeps creating snapshots.
  backup_schedule_skip_destroy = true

  tags = var.tags
}

output "cluster" {
  value = module.cluster
}
```

**Additional files needed:**
- [variables.tf](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v1.0.0/examples/16_cluster_with_last_n_copies/variables.tf)
- [versions.tf](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v1.0.0/examples/16_cluster_with_last_n_copies/versions.tf)


## Production Considerations
- This example enables recommended production settings by default, see the [Production Recommendations (Enabled By Default)](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v1.0.0/README.md#production-recommendations-enabled-by-default) for details.
- However, some recommendations must be manually set, see the [Production Recommendations (Manually Configured)](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v1.0.0/README.md#production-recommendations-manually-configured) list.

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

- You can use this and replace the `var.project_id` with `mongodbatlas_project.this.project_id` in the [main.tf](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v1.0.0/examples/16_cluster_with_last_n_copies/main.tf) file.
