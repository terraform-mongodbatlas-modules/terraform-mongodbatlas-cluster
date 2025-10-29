# Import Existing Clusters (Experimental)

⚠️ **Experimental Feature**: This example demonstrates how to import existing MongoDB Atlas clusters into Terraform management using the cluster module.

## Pre Requirements

If you are familiar with Terraform and already have clusters in MongoDB Atlas, go to [commands](#commands)

1. To run the `terraform` commands you need to install [Terraform](https://developer.hashicorp.com/terraform/install).
2. Sign up for a [MongoDB Atlas Account](https://www.mongodb.com/products/integrations/hashicorp-terraform)
3. Configure [authentication](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs#authentication)
4. An existing [MongoDB Atlas Project](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs/resources/project) with at least one cluster

## Commands

```sh
terraform init
# configure authentication env-vars (MONGODB_ATLAS_XXX)
# configure your `vars.tfvars` with `project_id={PROJECT_ID}`
terraform apply -var-file vars.tfvars
# This generates .tf files in the ./clusters/ directory
```

The generated files will be in `./clusters/` - one `.tf` file per cluster found in your project.

## Review and Refine Generated Configuration

After generation, follow these steps:

### 1. Review Generated Files

```sh
cd clusters
ls -la  # See generated cluster configuration files
```

### 2. Iterate to Achieve No Plan Changes

**Critical Step**: Before importing, you must refine the generated configuration until `terraform plan` shows no changes.

```sh
terraform plan  # Check what Terraform wants to change
# Adjust the generated .tf files as needed
# Repeat until you see "No changes. Your infrastructure matches the configuration."
```

See [clusters/README.md](./clusters/README.md) for detailed guidance on this iterative process.

### 3. Import Clusters

Once plan shows no changes:

```sh
terraform apply  # Execute the import blocks
```

### 4. Verify

```sh
terraform plan  # Should show "No changes"
```

## What Gets Generated

For each cluster in your project, a `.tf` file is created with:

- **Import block** - Associates the existing cluster with the Terraform module
- **Module configuration** - Uses the cluster module with your existing cluster settings
- **Output block** - Exposes connection strings

Example generated file structure:

```hcl
import {
  id = "${var.project_id}-my-cluster"
  to = module.my_cluster.mongodbatlas_advanced_cluster.this
}

module "my_cluster" {
  source = "../../../"
  
  project_id   = var.project_id
  name         = "my-cluster"
  cluster_type = "REPLICASET"
  
  regions = [
    {
      name       = "US_EAST_1"
      node_count = 3
    },
  ]
  
  provider_name = "AWS"
  instance_size = "M10"
}

output "my_cluster_connection_strings" {
  description = "Connection strings for my-cluster"
  value       = module.my_cluster.connection_strings
}
```

## Important Notes

- **Experimental**: Generated configuration may require manual adjustments
- **Test first**: Use a non-production project for initial testing
- **Defaults omitted**: The generator attempts to omit default values, but you may need to add fields that differ from module defaults
- **Iterative process**: Achieving a clean import requires iteration - see [clusters/README.md](./clusters/README.md)

## Feedback or Help

- If you have any feedback or trouble please open a Github Issue
