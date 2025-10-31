<!-- This file is used to generate the examples/README.md files -->
# Cluster using the `replication_specs` to define Cluster Topology

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
module "replication_var" {
  source  = "terraform-mongodbatlas-modules/cluster/mongodbatlas"

  name         = "replication-var"
  project_id   = var.project_id
  regions      = []
  cluster_type = "SHARDED"
  replication_specs = [{
    region_configs = [{
      priority      = 7
      provider_name = "AWS"
      region_name   = "US_EAST_1"
      shard_number  = 1
      electable_specs = {
        instance_size = "M10"
        node_count    = 3
      }
    }]
  }]
  tags = var.tags
}
```

**Additional files needed:**
- [variables.tf](./variables.tf)
- [versions.tf](./versions.tf)


## Production Considerations
- This example enables recommended production settings by default, see the [Production Recommendations (Enabled By Default)](../../README.md#production-recommendations-enabled-by-default) for details.
- However, some recommendations must be manually set, see the [Production Recommendations (Manually Configured)](../../README.md#production-recommendations-manually-configured) list.

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

- You can use this and replace the `var.project_id` with `mongodbatlas_project.this.project_id` in the [main.tf](./main.tf) file.
