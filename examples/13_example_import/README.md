# Cluster Import Example

Generate Terraform configuration from existing MongoDB Atlas clusters.

## Quick Start

```bash
cd examples/13_example_import

# Import a specific cluster by name
terraform init
terraform apply -var="project_id=YOUR_PROJECT_ID" -var="cluster_name=my-cluster"

# The cluster configuration is automatically written to {cluster-name}.tf
```

## What It Does

This module:
1. Fetches cluster data from MongoDB Atlas by name
2. Transforms it into clean Terraform configuration
3. Automatically writes it to `{cluster-name}.tf` in the specified directory

## Usage

### Basic Usage

```hcl
module "import_cluster" {
  source = "./modules/cluster_import"

  cluster_name     = "my-production-cluster"
  project_id       = "664619d870c247237f4b86a6"
  output_directory = path.module
}
```

### Custom Filename

```hcl
module "import_cluster" {
  source = "./modules/cluster_import"

  cluster_name     = "my-cluster"
  project_id       = var.project_id
  output_directory = path.module
  filename         = "imported-cluster"  # Creates imported-cluster.tf
}
```

### Import Multiple Clusters

```hcl
locals {
  clusters = ["prod-cluster", "staging-cluster", "dev-cluster"]
}

module "import_clusters" {
  for_each = toset(local.clusters)

  source = "./modules/cluster_import"

  cluster_name     = each.value
  project_id       = var.project_id
  output_directory = "${path.module}/imported"
}
```

## Smart Filtering

The generated configuration only includes values that matter, automatically filtering out:

### Defaults
- ✅ `auto_scaling` with default values (enabled, M10-M200, disk auto-scaling)
- ✅ `backup_enabled = true` / `pit_enabled = true` / `redact_client_log_data = true`
- ✅ `version_release_system = "LTS"` (default)
- ✅ Advanced configuration fields matching defaults

### Auto-Scaling Related
- ✅ `disk_size_gb` when disk auto-scaling is enabled
- ✅ `instance_size` when compute auto-scaling is enabled
- ✅ `instance_size_analytics` when no analytics nodes exist

### Provider-Specific
- ✅ `ebs_volume_type` and `disk_iops` when not using PROVISIONED volumes

### Empty Values
- ✅ Empty `tags = {}`
- ✅ Zero node counts
- ✅ Null/empty strings

## Example Output

For a basic M10 replica set:

```hcl
# Auto-generated from existing cluster: my-cluster
# Cluster Type: REPLICASET
# Generated: 2025-10-28T12:00:00Z

module "my_cluster" {
  source = "../../"

  project_id = var.project_id

  name         = "my-cluster"
  cluster_type = "REPLICASET"

  regions = [
    {
      name          = "US_EAST_1"
      node_count    = 3
      instance_size = "M10"
    },
  ]

  provider_name = "AWS"
  instance_size = "M10"

  # Clean output - only non-default values shown
  backup_enabled = false  # Only shown because it differs from default (true)
}

# Outputs
output "my_cluster_connection_strings" {
  description = "Connection strings for my-cluster"
  value       = module.my_cluster.connection_strings
  sensitive   = true
}
```

## Module Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `cluster_name` | **Yes** | - | Name of the cluster to import. |
| `project_id` | **Yes** | - | MongoDB Atlas project ID. |
| `output_directory` | **Yes** | - | Directory where the .tf file will be written. |
| `filename` | No | cluster name | Custom filename (without .tf extension). |

## Use Cases

1. **Import existing clusters** into Terraform management
2. **Document cluster configuration** in version control
3. **Clone clusters** with slight modifications
4. **Migrate clusters** between projects/accounts
5. **Generate IaC from UI-created clusters**

## Architecture

```text
13_example_import/
├── main.tf                      # Example usage (by name or first cluster)
├── outputs.tf                   # Simple outputs
└── modules/
    └── cluster_import/          # Self-contained import module
        ├── main.tf              # Data source, transformation, file generation
        ├── variables.tf         # Flexible input options
        ├── outputs.tf           # Filtered outputs
        └── README.md            # Module documentation
```

## Requirements

- Terraform >= 1.6
- mongodbatlas provider ~> 2.0
- local provider 2.4.1
- MongoDB Atlas credentials configured

## Notes

- Generated files include timestamp and cluster metadata as comments
- Module name in generated file: `{cluster_name_with_underscores}`
- Output name: `{cluster_name_with_underscores}_connection_strings`
- File is written during `terraform apply`, not `terraform plan`
