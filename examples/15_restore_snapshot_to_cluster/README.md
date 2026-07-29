<!-- @generated
WARNING: This file is auto-generated. Do not edit directly.
Changes will be overwritten when documentation is regenerated.
Run 'just gen-examples' to regenerate.
-->
# Restore a Cluster from a Backup Snapshot (`cloud_backup_snapshot_restore_job`, automated + point-in-time)

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
module "source" {
  source  = "terraform-mongodbatlas-modules/cluster/mongodbatlas"
  version = "v0.4.0"

  name         = "restore-source"
  project_id   = var.project_id
  cluster_type = "REPLICASET"
  regions = [
    {
      name       = "US_EAST_1"
      node_count = 3
    }
  ]
  provider_name = "AWS"

  # ON_DEMAND keeps this example focused on the manual snapshot + restore job below, instead of
  # also provisioning the default recurring schedule (see docs/backup_guide.md).
  backup_mode = "ON_DEMAND"

  tags = var.tags
}

module "target" {
  source  = "terraform-mongodbatlas-modules/cluster/mongodbatlas"
  version = "v0.4.0"

  name         = "restore-target"
  project_id   = var.project_id
  cluster_type = "REPLICASET"
  regions = [
    {
      name       = "US_EAST_1"
      node_count = 3
    }
  ]
  provider_name = "AWS"

  backup_mode = "ON_DEMAND"

  tags = var.tags
}

# On-demand snapshot; use backup_mode/backup_retention instead for a recurring schedule (see docs/backup_guide.md).
resource "mongodbatlas_cloud_backup_snapshot" "this" {
  project_id        = var.project_id
  cluster_name      = module.source.cluster_name
  description       = "On-demand snapshot for the restore-job example"
  retention_in_days = 2
}

# Restore jobs are one-off actions, not module-managed. Restoring wipes all existing data on the target cluster.
resource "mongodbatlas_cloud_backup_snapshot_restore_job" "this" {
  project_id   = var.project_id
  cluster_name = module.source.cluster_name
  snapshot_id  = mongodbatlas_cloud_backup_snapshot.this.snapshot_id

  delivery_type_config {
    # Set var.restore_point_in_time_utc_seconds to restore to a specific instant (point-in-time)
    # instead of the snapshot as-is (automated). See docs/backup_guide.md for the third delivery
    # type, download, which isn't modeled here.
    automated                 = var.restore_point_in_time_utc_seconds == null
    point_in_time             = var.restore_point_in_time_utc_seconds != null
    target_cluster_name       = module.target.cluster_name
    target_project_id         = var.project_id
    point_in_time_utc_seconds = var.restore_point_in_time_utc_seconds
  }
}

output "source_cluster" {
  value = module.source
}

output "target_cluster" {
  value = module.target
}
```

**Additional files needed:**
- [variables.tf](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.4.0/examples/15_restore_snapshot_to_cluster/variables.tf)
- [versions.tf](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.4.0/examples/15_restore_snapshot_to_cluster/versions.tf)


## Production Considerations
- This example enables recommended production settings by default, see the [Production Recommendations (Enabled By Default)](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.4.0/README.md#production-recommendations-enabled-by-default) for details.
- However, some recommendations must be manually set, see the [Production Recommendations (Manually Configured)](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.4.0/README.md#production-recommendations-manually-configured) list.

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

- You can use this and replace the `var.project_id` with `mongodbatlas_project.this.project_id` in the [main.tf](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.4.0/examples/15_restore_snapshot_to_cluster/main.tf) file.
