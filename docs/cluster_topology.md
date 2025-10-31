# MongoDB Atlas Cluster Topology Configuration Guide

This guide explains how to configure cluster topology in the MongoDB Atlas Terraform Cluster Module. Understanding these configuration options will help you choose the right approach for your deployment needs.

## Table of Contents

- [Introduction](#introduction)
- [Understanding the Two Configuration Approaches](#understanding-the-two-configuration-approaches)
- [When Should You Use Each Approach?](#when-should-you-use-each-approach)
- [Key Variables Reference](#key-variables-reference)
- [Configuration Examples](#configuration-examples)
- [Migrating from regions to replication_specs](#migrating-from-regions-to-replication_specs)
- [Important Considerations](#important-considerations)
- [Additional Resources](#additional-resources)

## Introduction

The MongoDB Atlas Terraform Cluster Module provides two ways to configure cluster topology:

1. **Simplified Configuration** using the `regions` variable (recommended for most users)
2. **Direct Configuration** using the `replication_specs` variable (for advanced use cases)

Both approaches manage the same underlying `mongodbatlas_advanced_cluster` resource, but offer different levels of abstraction and control. This guide will help you understand the differences and choose the right approach for your needs.

## Understanding the Two Configuration Approaches

### Simplified Configuration (`regions` variable)

The simplified configuration approach uses the `regions` variable to define your cluster topology. This is the **recommended approach** for most users.

**What it is:**
- A module-managed abstraction that automatically generates the underlying `replication_specs` configuration
- Handles complexity behind the scenes while providing a clean, intuitive interface

**Key features:**
- Automatic `replication_specs` generation from simple region definitions
- Auto-scaling enabled by default (M10-M200 range) for production-ready deployments
- Simplified shard management using `shard_count` for uniform topologies
- Built-in validation with clear error messages to guided configuration
- Automatic persistence of instance sizes between plan/apply cycles when using auto-scaling

**Example:**
```hcl
module "cluster" {
  source = "terraform-mongodbatlas-modules/cluster/mongodbatlas"
  
  project_id   = var.project_id
  name         = "my-cluster"
  cluster_type = "SHARDED"
  
  regions = [
    { name = "US_EAST_1", node_count = 3 },
    { name = "US_WEST_2", node_count = 2 }
  ]
  
  # Auto-scaling enabled by default
  # Instance sizes managed automatically
}
```

### Direct Configuration (`replication_specs` variable)

The direct configuration approach uses the `replication_specs` variable to pass configuration directly to the underlying resource.

**What it is:**
- A direct passthrough to the `mongodbatlas_advanced_cluster` resource's `replication_specs` attribute
- Provides full control over all resource attributes without abstraction

**Key features:**
- Full control over all resource configuration details
- Use the exact schema from the provider documentation
- Easier migration path from existing `mongodbatlas_advanced_cluster` resources
- Ideal for users already familiar with the resource schema

**Important limitations:**
- Cannot be used with `auto_scaling` in the current version (support planned for future release)
  - Reason: Direct passthrough bypasses the data source logic required for auto-scaling
- Cannot be combined with ANY simplified variables (`regions`, `shard_count`, `instance_size`, etc.)
- Requires explicitly setting `regions = []` to disable simplified configuration

**Example:**
```hcl
module "cluster" {
  source = "terraform-mongodbatlas-modules/cluster/mongodbatlas"
  
  project_id   = var.project_id
  name         = "my-cluster"
  cluster_type = "SHARDED"
  
  regions = []  # Required: explicitly disable simplified config
  
  replication_specs = [
    {
      num_shards = 1
      region_configs = [
        {
          electable_specs = {
            instance_size = "M30"
            node_count    = 3
          }
          priority      = 7
          provider_name = "AWS"
          region_name   = "US_EAST_1"
        }
      ]
    }
  ]
}
```

### Mutual Exclusivity

You must choose ONE configuration approach per cluster - these approaches cannot be mixed:

- **Option A:** Use `regions` + other simplified variables (recommended)
- **Option B:** Use `replication_specs` with `regions = []` (no simplified variables allowed)

The module validates your configuration and provides clear error messages if you attempt to mix approaches. All other resource variables (such as `backup_enabled`, `termination_protection_enabled`, `tags`, etc.) can be used with either approach.

## When Should You Use Each Approach?

### Decision Guide

**Use `regions` (simplified configuration) if you:**

- Are creating a new cluster deployment  
- Want auto-scaling capabilities (recommended for production)  
- Prefer module-managed configuration that handles complexity

**Use `replication_specs` (direct configuration) if you:**

- Are migrating from an existing `mongodbatlas_advanced_cluster` resource  
- Already have working `replication_specs` configuration to reuse  
- Need manual scaling control only (auto-scaling not supported)  
- Prefer working directly with the provider schema

## Key Variables Reference

### Simplified Configuration Variables

When using the simplified `regions` approach, these variables are available:

#### Core Topology Variables

- **`cluster_type`** (required) - Type of cluster topology
  - Valid values: `REPLICASET`, `SHARDED`, or `GEOSHARDED`
  
- **`regions`** - List of region configurations defining your cluster topology
  - See [Per-Region Configuration Options](#per-region-configuration-options) below
  
- **`shard_count`** (optional) - Number of uniform shards to create
  - Each shard will contain all regions defined in `regions`
  - Auto-scaling continues to use [Independent Shard Scaling (ISS)](https://www.mongodb.com/docs/atlas/cluster-autoscaling/#scaling-a-sharded-cluster)
  - Cannot be used with manual Independent Shard Scaling (ISS) since each shard must be set explicitly

#### Scaling & Sizing

- **`auto_scaling`** - Auto-scaling configuration (enabled by default)
  - Default range: M10-M200 (works across AWS/Azure/GCP)
  - Can override min/max instance sizes
  - Set to `null` to disable auto-scaling
  
- **`instance_size`** - Instance size to use at root level
  - Only applicable when auto-scaling is disabled
  - Can be overridden per-region for Independent Shard Scaling

#### Per-Region Configuration Options

Within each item in the `regions` list, you can specify:

- **`name`** (required) - Cloud provider region identifier
  - Examples: `"US_EAST_1"`, `"EU_WEST_1"`, `"ASIA_SOUTH_1"`
  
- **`node_count`** - Number of electable (voting) nodes in the region
  - Default: `3` (recommended for production high availability)
  
- **`node_count_read_only`** - Number of read-only nodes
  - Optional: Add read-only nodes for read scaling
  
- **`node_count_analytics`** - Number of analytics nodes
  - Optional: Add analytics nodes for analytics workloads
  - Note: See [Analytics Node Scaling Limitations](#analytics-node-scaling-limitations)
  
- **`instance_size`** - Instance size override for this region
  - Used for Independent Shard Scaling (ISS) with manual scaling
  - Example: `"M30"`, `"M40"`, `"R50"`
  
- **`shard_number`** - Explicit shard assignment
  - Required for SHARDED/GEOSHARDED clusters when using ISS
  - Not used when using `shard_count`
  
- **`zone_name`** - Geographic zone identifier
  - Required for GEOSHARDED clusters
  - Example: `"US"`, `"EU"`, `"APAC"`
  
- **`disk_iops`** - Provisioned IOPS for EBS volumes
  - Only valid when disk auto-scaling is disabled
  
- **`disk_size_gb`** - Disk size in gigabytes
  - Only valid when disk auto-scaling is disabled
  
- **`ebs_volume_type`** - EBS volume type (AWS only)
  - Only valid when disk auto-scaling is disabled
  - Valid values: `"STANDARD"`, `"PROVISIONED"`

**Important:** These simplified variables CANNOT be used when using `replication_specs`.

### Direct Configuration Variable

When using the direct `replication_specs` approach:

#### Resource Passthrough

- **`replication_specs`** - Direct mapping to `mongodbatlas_advanced_cluster.replication_specs`
  - Refer to [provider documentation](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs/resources/advanced_cluster#replication_specs) for complete schema details
  - **Must set:** `regions = []` to explicitly disable simplified configuration
  - **Cannot be combined with:** `regions`, `shard_count`, `auto_scaling`, or `instance_size`
  - All instance sizing and scaling configuration is embedded within the `replication_specs` structure itself

## Configuration Examples

This module includes multiple working examples demonstrating different deployment patterns.

### Simplified Approach (`regions`) Examples

Most examples in this repository use the simplified `regions` approach. Refer to the [Examples section in the main README](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.1.0/README.md#examples) which provides two organized tables:

- **Getting Started Examples** - Production and development cluster configurations
- **Advanced Examples** - Multi-region, multi-cloud, sharded topologies, analytics nodes, and more

### Direct Approach (`replication_specs`) Example

See [`examples/09_cluster_using_replication_specs`](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.1.0/examples/09_cluster_using_replication_specs) for a complete example of using the `replication_specs` variable directly with manual scaling.

## Migrating from `regions` to `replication_specs`

You might want to migrate from the simplified `regions` approach to direct `replication_specs` if you need:
- Configurations not supported by the simplified variables
- More granular control over specific resource attributes
- Manual scaling control for specific requirements

### Migration Steps

**1. Read current cluster state:**

First, add a data source to read your existing cluster configuration:

```hcl
data "mongodbatlas_advanced_cluster" "existing" {
  project_id = var.project_id
  name       = module.cluster.name
}
```

**2. Extract replication_specs from data source:**

Add an output to view the current `replication_specs` structure:

```hcl
output "current_replication_specs" {
  value = data.mongodbatlas_advanced_cluster.existing.replication_specs
}
```

Run `terraform apply` and note the output. This shows you the exact `replication_specs` configuration to use.

**3. Update module configuration:**

Modify your module configuration to use `replication_specs`:

```hcl
module "cluster" {
  source = "terraform-mongodbatlas-modules/cluster/mongodbatlas"
  
  project_id   = var.project_id
  name         = "my-cluster"
  cluster_type = "SHARDED"
  
  # Disable simplified configuration
  regions = []
  
  # Remove: regions list
  # Remove: shard_count
  # Remove: auto_scaling
  # Remove: instance_size (at root level)
  
  # Add extracted replication_specs
  replication_specs = [
    # Paste the configuration from step 2
  ]
  
  # Keep other variables (backup_enabled, tags, etc.)
}
```

**4. Verify no changes:**

Run a plan to ensure Terraform doesn't detect any changes to the cluster:

```bash
terraform plan
# Should show: No changes. Your infrastructure matches the configuration.
```

**5. Apply configuration:**

If the plan shows no changes (or only expected changes), apply:

```bash
terraform apply
```

Your cluster is now using the `replication_specs` approach and you can modify the configuration as needed.

## Important Considerations

### Auto-scaling Limitations

Auto-scaling is only available when using the simplified `regions` configuration approach.

**Current limitation:**
- Cannot use `auto_scaling` with `replication_specs` in the current module version
- When using `replication_specs`, you must manage instance sizes manually within the specs

**Future support:**
- Auto-scaling with `replication_specs` is planned for a future module version
- This will provide auto-scaling capabilities regardless of configuration approach

**Workaround:**
If you need auto-scaling, use the `regions` approach. If you need direct `replication_specs` control, use manual scaling.

### Manual Scaling with Different Instance Sizes (ISS)

Independent Shard Scaling (ISS) allows different shards to have different instance sizes. This is useful for:
- Cost optimization by sizing shards based on their data and workload
- Gradual scaling of specific shards without affecting others
- Testing new instance sizes on a subset of shards

**Requirements for ISS:**
- Must explicitly specify `instance_size` for each region
- Must explicitly specify `shard_number` for each region
- Cannot use `shard_count` (which creates uniform shards)
- Must disable auto-scaling (set `auto_scaling = {compute_enabled = false}`)
- See example in [Production Cluster with Manual Scaling](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.1.0/examples/02_production_cluster_with_manual_scaling)

### Disk Configuration Variables

The disk-related variables (`disk_iops`, `disk_size_gb`, `ebs_volume_type`) can only be used when disk auto-scaling is disabled.

**When using auto-scaling (default):**
- Disk configuration is managed automatically by Atlas
- You cannot manually specify disk variables
- Atlas will scale disk capacity and IOPS as needed

**For manual disk configuration:**
1. Disable disk auto-scaling, set `auto_scaling = {disk_gb_enabled = false}`
2. Specify disk variables as needed (`disk_size_gb`, `disk_iops`, etc.)

This applies to both the `regions` and `replication_specs` configuration approaches.

### Analytics Node Scaling Limitations

When using the `regions` variable with **manual scaling**, there is a limitation regarding analytics nodes:

**Limitation:**
- Analytics nodes (`node_count_analytics`) will use the same storage configuration as electable nodes
- Cannot configure different instance sizes or disk settings for analytics nodes independently
- The following analytics-specific variables are not supported in the simplified configuration:
  - `instance_size_analytics`
  - `disk_iops_analytics`

**When this matters:**
- If you need analytics nodes with different storage characteristics than electable nodes
- For example: less compute for analytics workloads, or different IOPS settings

**Workaround:**
If you need independent storage configuration for analytics nodes, use the `replication_specs` variable instead, which supports the full resource schema including analytics-specific settings.

**Note:** This limitation does NOT apply when using auto-scaling (the default), as storage is managed automatically by Atlas based on workload requirements.

### Configuration Persistence with Auto-scaling

When using the simplified `regions` approach with auto-scaling enabled, the module automatically handles configuration persistence:

**How it works:**
- The module uses a `data.mongodbatlas_advanced_cluster` data source internally
- This reads the current cluster state before each plan/apply
- Instance sizes that may have changed due to auto-scaling are preserved
- Prevents unwanted configuration drift in your Terraform state

**Benefits:**
- No need to use `lifecycle.ignore_changes` blocks
- Clean Terraform plans that show only actual configuration changes
- Auto-scaling can adjust instance sizes without causing plan differences

**Example scenario:**
1. You deploy a cluster with auto-scaling (M10-M60 range)
2. Atlas auto-scales the cluster to M40 due to workload
3. Running `terraform plan` shows no changes (not trying to scale back to M10)
4. Your configuration remains clean and maintainable

This automatic persistence is one of the key benefits of using the simplified configuration approach.

### Validation & Error Messages

The module validates your configuration and provides specific error messages to help you fix issues quickly:

**Common validation checks:**
- Ensuring `regions` and `replication_specs` are not used together
- Verifying that simplified variables are not used with `replication_specs`
- Checking that `regions = []` is set when using `replication_specs`
- Validating cluster type combinations and required fields

**Error message examples:**
```
Error: Cannot use both 'regions' and 'replication_specs'
Please choose one topology configuration method.
```

```
Error: When using 'replication_specs', you must set 'regions = []'
The simplified regions configuration must be explicitly disabled.
```

For troubleshooting common issues and additional help, see the FAQ and Troubleshooting sections in the [main README](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.1.0/README.md#faq).

## Additional Resources

- **[Main Module README](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.1.0/README.md)** - Complete module documentation with all variables and outputs
- **[Examples Directory](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.1.0/examples)** - Working examples for all deployment patterns
- **[Provider Documentation](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs/resources/advanced_cluster)** - Complete resource schema reference
- **[MongoDB Atlas Documentation](https://www.mongodb.com/docs/atlas/)** - Official Atlas documentation

---

**Questions or feedback?** Please open an issue in the [GitHub repository](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/issues).
