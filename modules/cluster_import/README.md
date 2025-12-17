# Cluster Import Helper Module (Experimental)

⚠️ **Experimental Feature**: This module is under active development. The generated configuration may require manual adjustments.

## Overview

This module helps migrate existing MongoDB Atlas clusters to use the cluster module by:
- Reading your existing cluster configuration from the MongoDB Atlas API
- Generating Terraform configuration files in the cluster module format
- Creating import blocks to bring existing clusters under Terraform management

## Pre Requirements

1. Install [Terraform](https://developer.hashicorp.com/terraform/install)
2. Configure [authentication](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs#authentication)
3. Have existing clusters in MongoDB Atlas that you want to import

## Usage Steps

### 1. Configure the Import Module

Create a `main.tf` file that uses this module to import a specific cluster:

```hcl
module "cluster_import" {
  source = "../../modules/cluster_import"
  
  cluster_name     = "my-cluster-name"
  project_id       = var.project_id
  output_directory = "./clusters"
}
```

To import multiple clusters, use `for_each`:

```hcl
data "mongodbatlas_advanced_clusters" "this" {
  project_id = var.project_id
}

module "cluster_import" {
  for_each = {
    for cluster in data.mongodbatlas_advanced_clusters.this.results : cluster.name => cluster
  }
  
  source = "../../modules/cluster_import"
  
  cluster_name     = each.key
  project_id       = var.project_id
  output_directory = "./clusters"
}
```

### 2. Generate Configuration Files

```sh
terraform init
# configure authentication env-vars (MONGODB_ATLAS_XXX)
terraform apply -var="project_id=YOUR_PROJECT_ID"
```

This will create `.tf` files in the `./clusters/` directory, one per cluster.

### 3. Review and Adjust Generated Configuration

- Review each generated file in `./clusters/`
- The module attempts to omit default values, but you may need to adjust the configuration
- **Goal**: Achieve an empty plan (`No changes`) before importing
- Run `terraform plan` iteratively and add/remove fields as needed to match your existing cluster

### 4. Import Clusters

Once your plan shows no changes:

```sh
terraform apply  # This will execute the import blocks
```

### 5. Verify Import

```sh
terraform plan  # Should show "No changes"
```

## What This Module Does

- Flattens complex `replication_specs` into the module's simplified `regions` format
- Filters out default values to keep configuration minimal
- Handles different cluster types (REPLICASET, SHARDED, GEOSHARDED)
- Extracts common settings to module-level variables when possible
- Generates `import` blocks for Terraform

## Important Notes

- Generated configuration is a starting point - manual review is required
- Some cluster configurations may require additional adjustments
- Test in a non-production environment first
- See the [example](../../examples/13_example_import/) for a complete working example
