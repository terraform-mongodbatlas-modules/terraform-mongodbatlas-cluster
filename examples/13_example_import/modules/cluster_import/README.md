# Cluster Import Transformation Module

This submodule contains the core logic for transforming MongoDB Atlas cluster data source output into the cluster module's variable format.

## Purpose

This module performs the heavy lifting of:
1. Flattening nested `replication_specs[].region_configs[]` into a flat `regions` list
2. Filtering out null values and empty strings
3. Removing values that match module defaults to keep configuration clean
4. Handling cluster-type-specific logic (REPLICASET, SHARDED, GEOSHARDED)

## Inputs

- `cluster`: Complete cluster object from `mongodbatlas_advanced_clusters` data source

## Outputs

All outputs are filtered to exclude null values and values matching module defaults:

- `name`: Cluster name
- `regions`: Transformed regions list
- `provider_name`: Common provider (if all regions use same)
- `instance_size`: Instance size (if not auto-scaling)
- `disk_size_gb`: Disk size
- `disk_iops`: Disk IOPS
- `ebs_volume_type`: EBS volume type
- `instance_size_analytics`: Analytics instance size
- `auto_scaling`: Auto-scaling config (null if matches defaults)
- `auto_scaling_analytics`: Analytics auto-scaling config
- `tags`: Tags (null if empty)
- `shard_count`: Shard count (for uniform shards)
- Plus additional cluster properties

## Default Filtering

The module filters out these defaults:

### Auto Scaling
If auto_scaling matches ALL of these defaults, it returns null:
- `compute_enabled = true`
- `compute_max_instance_size = "M200"` (or empty)
- `compute_min_instance_size = "M10"` (or empty)
- `compute_scale_down_enabled = true`
- `disk_gb_enabled = true`

### Resource Defaults
- `backup_enabled = true` → null
- `pit_enabled = true` → null
- `redact_client_log_data = true` → null

### Advanced Configuration Defaults
- `default_write_concern = "majority"` → null
- `javascript_enabled = false` → null
- `minimum_enabled_tls_protocol = "TLS1_2"` → null
- `tls_cipher_config_mode = "DEFAULT"` → null

### Empty Values
- Empty strings → null
- Zero values → null
- Empty lists/sets → null
- Empty maps → null (for most fields) or {} (for tags)

## Logic Details

### Cluster Type Handling

**REPLICASET**:
- `shard_number` → null on all regions
- `zone_name` → null on all regions
- `shard_count` → null

**SHARDED**:
- `shard_number` → index of shard (0, 1, 2...)
- `zone_name` → null on all regions
- `shard_count` → number of shards (only if all shards have identical topology)

**GEOSHARDED**:
- `shard_number` → preserved per zone
- `zone_name` → from replication_spec
- `shard_count` → null

### Common Values Extraction

The module extracts common values that apply to all regions:
- `provider_name`: Set if all regions use same provider
- `instance_size`: From first electable region (if not auto-scaling)
- `disk_size_gb`: From first electable region
- `disk_iops`: From first electable region (if > 0)
- `ebs_volume_type`: From first electable region

This allows cleaner configuration at the module level rather than repeating values in each region.
