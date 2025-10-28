# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Terraform module for simplifying MongoDB Atlas cluster deployments. It wraps the `mongodbatlas_advanced_cluster` resource and provides two configuration approaches:
1. **Simplified `regions` variable** (recommended) - Flattened schema with helper variables like `shard_count` and `auto_scaling`
2. **Direct `replication_specs` variable** - For users familiar with the Atlas provider's nested schema

The module is currently in **public preview (v0)** and will reach v1 with long-term upgrade support in early next year.

## Key Commands

### Development Workflow
All commands are managed through `just` (command runner):

```bash
# Format all Terraform files
just fmt

# Validate configuration
just validate

# Lint with TFLint
just lint

# Generate documentation (uses .terraform-docs.yml)
just docs

# Run all checks (format, validate, lint, docs)
just check

# Initialize all examples
just init-examples

# Plan all examples (requires MongoDB Atlas project ID)
just plan-examples <project-id>
```

### Testing

Set environment variables for authentication:
```bash
export MONGODB_ATLAS_CLIENT_ID=your_sa_client_id
export MONGODB_ATLAS_CLIENT_SECRET=your_sa_client_secret
export MONGODB_ATLAS_ORG_ID=your_org_id
```

Run tests:
```bash
# Run only unit/plan tests (no resources created)
just unit-plan-tests

# Run integration/apply tests (creates and destroys resources)
just integration-tests

# Run all tests
just test
```

**Important for apply tests:** Set `termination_protection_enabled = false` in test configurations to allow cleanup.

## Module Architecture

### Core Files

- **`main.tf`** - Core module logic with complex transformation from simplified `regions` to `replication_specs`
- **`variables_module.tf`** - Simplified module-specific variables (`regions`, `shard_count`, `auto_scaling`, etc.)
- **`variables_resource.tf`** - Direct pass-through variables from `mongodbatlas_advanced_cluster` resource
- **`data_cluster_read.tf`** - Reads existing cluster state to handle auto-scaling instance_size changes
- **`output.tf`** - Module outputs (cluster_id, connection_strings, etc.)
- **`versions.tf`** - Provider requirements (mongodbatlas ~> 2.0, terraform >= 1.6)

### Cluster Topology Transformation Logic (main.tf)

The module's primary complexity is in `main.tf:1-251`, which transforms the simplified `regions` variable into the Atlas API's `replication_specs` format:

1. **Cluster Type Detection** (lines 6-9): Determines if cluster is REPLICASET, SHARDED, or GEOSHARDED
2. **Region Grouping** (lines 11-103): Groups regions into shards/zones based on cluster type:
   - **REPLICASET**: Single group with all regions
   - **SHARDED**: Groups by `shard_number` or creates uniform shards via `shard_count`
   - **GEOSHARDED**: Groups by `zone_name` and optionally `shard_number` within zones
3. **Auto-scaling Logic** (lines 105-132): Handles compute/disk auto-scaling configuration
4. **Replication Specs Generation** (lines 135-186): Builds the final `replication_specs` structure with:
   - Priority assignment (line 144): First region in each group gets priority 7, decreasing for subsequent regions
   - Instance size resolution for auto-scaling (lines 155-180): Reads existing cluster data to preserve auto-scaled sizes
   - Specs generation for electable/read-only/analytics nodes
5. **Validation** (lines 192-250): Comprehensive validation rules with detailed error messages

### Auto-scaling Instance Size Management

The module uses `data.mongodbatlas_advanced_clusters` (data_cluster_read.tf) to read the existing cluster state. This is critical because:
- When auto-scaling is enabled, Atlas may change `instance_size` values
- Without reading the existing state, Terraform would show plan changes when instance_size has been auto-scaled
- See lines 155-180 in main.tf where existing instance sizes are preserved

### Validation Strategy

The module has extensive input validation at two levels:
1. **Variable-level validation** (variables_module.tf): Basic constraints like allowed providers, minimum instance sizes
2. **Lifecycle preconditions** (main.tf:255-259): Complex cross-variable validations that run before resource creation

## Configuration Patterns

### Two Topology Options (Mutually Exclusive)

**Option 1: Simplified `regions` (recommended)**
```hcl
regions = [
  { name = "US_EAST_1", node_count = 3, provider_name = "AWS", shard_number = 1 }
]
```

**Option 2: Direct `replication_specs`**
```hcl
replication_specs = [
  {
    region_configs = [
      { region_name = "US_EAST_1", provider_name = "AWS", priority = 7, electable_specs = { node_count = 3, instance_size = "M10" } }
    ]
  }
]
```

When using `replication_specs`, set `regions = []` to avoid conflicts.

### Auto-scaling vs Manual Scaling

**Auto-scaling (enabled by default):**
```hcl
auto_scaling = {
  compute_enabled            = true
  compute_min_instance_size  = "M10"
  compute_max_instance_size  = "M200"
  disk_gb_enabled            = true
}
```

**Manual scaling:**
```hcl
auto_scaling = {
  compute_enabled = false
}
instance_size = "M30"  # Fixed size
```

Cannot mix: Setting `instance_size` when `auto_scaling.compute_enabled = true` causes validation error.

### Cluster Types

**REPLICASET**: Don't set `shard_number` or `zone_name` on regions
**SHARDED**: Set `shard_number` on each region OR use `shard_count` variable
**GEOSHARDED**: Set `zone_name` on each region (optionally `shard_number` for multi-shard zones)

### Production Defaults (Enabled)

The module enables MongoDB best practices by default:
- `backup_enabled = true`
- `pit_enabled = true` (continuous backups)
- `retain_backups_enabled = true`
- `redact_client_log_data = true`
- `advanced_configuration.default_write_concern = "majority"`
- `advanced_configuration.javascript_enabled = false`
- `advanced_configuration.minimum_enabled_tls_protocol = "TLS1_2"`

## Testing Structure

Tests are located in `/tests` directory:

**Plan tests** (no apply):
- `tests/plan_auto_scaling.tftest.hcl` - Validates auto-scaling configurations
- `tests/plan_regions.tftest.hcl` - Validates regions variable transformations
- `tests/plan_replication_spec.tftest.hcl` - Validates replication_specs option

**Apply tests** (creates resources):
- `tests/apply_regions.tftest.hcl` - Integration tests that create actual clusters

Test files use Terraform's native test framework (`terraform test`).

## Examples

Each example in `/examples` is self-contained with its own `main.tf`, `variables.tf`, `versions.tf`:
- `01_single_region_auto_scaling` - Production SHARDED cluster with auto-scaling
- `02_single_region_manual_scaling` - Production SHARDED cluster with fixed instance sizes
- `03_single_region_with_analytics` - Cluster with analytics nodes
- `04_multi_region_single_geo_replicaset` - Multi-region REPLICASET
- `05_multi_region_multi_geo` - SHARDED cluster across US+EU
- `06_multi_geo_sharded` - GEOSHARDED cluster
- `07_multi_cloud` - Multi-cloud (AWS+AZURE) cluster
- `08_dev` - Development REPLICASET cluster
- `09_replication_var` - Using `replication_specs` variable directly
- `10_multi_shard_multi_geo` - Advanced GEOSHARDED with multiple shards per zone
- `11_regions_helper` - Meta-module example (S/M/L cluster sizes)
- `12_multi_shard_uniform_topology` - SHARDED with `shard_count`

Examples share common tags via `examples/tags.tfvars`.

## Provider Metadata

The module tracks usage via `provider_meta "mongodbatlas"` (versions.tf:12-15):
- Sets `module_name = "cluster"` and `module_version = "0.1.0"`
- Appears in User-Agent header (view with `export TF_LOG=debug`)
- No sensitive configuration data is sent

## Common Development Pitfalls

1. **Auto-scaling conflicts**: Don't set `instance_size`, `disk_size_gb`, `disk_iops`, or `ebs_volume_type` when auto-scaling is enabled
2. **Region priority**: First region in each shard/zone gets highest priority (7). Order matters.
3. **SHARDED cluster**: Either use `shard_count` OR set `shard_number` on all regions, not both
4. **GEOSHARDED validation**: Within a zone, either all regions have `shard_number` or none do
5. **M0/M2/M5 not supported**: Module requires M10+ instance sizes
6. **Testing cleanup**: Always set `termination_protection_enabled = false` in apply tests

## Documentation Generation

Documentation is partially automated via `terraform-docs`:
- Configuration: `.terraform-docs.yml`
- README sections with `<!-- BEGIN_TF_DOCS -->` and `<!-- END_TF_DOCS -->` are auto-generated
- Some generation steps (inputs.md, TOC) are in alpha phase and may change
