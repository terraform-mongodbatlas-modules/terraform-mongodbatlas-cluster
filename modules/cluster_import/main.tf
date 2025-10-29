# Fetch cluster data by name
data "mongodbatlas_advanced_cluster" "this" {
  project_id = var.project_id
  name       = var.cluster_name
}

locals {
  # Use fetched cluster data
  cluster = data.mongodbatlas_advanced_cluster.this

  # Module defaults to compare against
  module_defaults = {
    auto_scaling = {
      compute_enabled            = true
      compute_max_instance_size  = "M200"
      compute_min_instance_size  = "M10"
      compute_scale_down_enabled = true
      disk_gb_enabled            = true
    }
    tags                   = {}
    backup_enabled         = true
    pit_enabled            = true
    redact_client_log_data = true
    advanced_configuration = {
      default_write_concern        = "majority"
      javascript_enabled           = false
      minimum_enabled_tls_protocol = "TLS1_2"
    }
  }

  # Flatten all region_configs from all replication_specs with shard/zone information
  all_regions_with_shard_info = flatten([
    for shard_idx, spec in local.cluster.replication_specs : [
      for region_idx, region_config in spec.region_configs : {
        # Basic region info
        name          = region_config.region_name
        provider_name = region_config.provider_name
        priority      = region_config.priority

        # Node counts
        node_count           = region_config.electable_specs.node_count
        node_count_read_only = region_config.read_only_specs.node_count
        node_count_analytics = region_config.analytics_specs.node_count

        # Instance sizes
        instance_size           = region_config.electable_specs.instance_size
        instance_size_analytics = region_config.analytics_specs.instance_size

        # Disk configuration
        disk_size_gb    = region_config.electable_specs.disk_size_gb
        disk_iops       = region_config.electable_specs.disk_iops
        ebs_volume_type = region_config.electable_specs.ebs_volume_type

        # Auto scaling
        auto_scaling           = region_config.auto_scaling
        analytics_auto_scaling = region_config.analytics_auto_scaling

        # Shard and zone information
        shard_number = shard_idx
        zone_name    = spec.zone_name != "" ? spec.zone_name : null
      }
    ]
  ])

  # Determine cluster type
  cluster_type  = local.cluster.cluster_type
  is_replicaset = local.cluster_type == "REPLICASET"
  is_sharded    = local.cluster_type == "SHARDED"
  is_geosharded = local.cluster_type == "GEOSHARDED"

  # Determine shard_count for SHARDED clusters (if all shards have same topology)
  shard_count = local.is_sharded ? length(local.cluster.replication_specs) : null

  # Auto scaling configuration from first region
  auto_scaling_raw                       = local.first_electable_region.auto_scaling
  auto_scaling_compute_enabled           = local.auto_scaling_raw != null && local.auto_scaling_raw.compute_enabled
  auto_scaling_disk_enabled              = local.auto_scaling_raw != null && local.auto_scaling_raw.disk_gb_enabled
  analytics_auto_scaling                 = local.first_analytics_region != null ? local.first_analytics_region.analytics_auto_scaling : null
  auto_scaling_compute_analytics_enabled = local.analytics_auto_scaling != null && local.analytics_auto_scaling.compute_enabled
  auto_scaling_disk_analytics_enabled    = local.analytics_auto_scaling != null && local.analytics_auto_scaling.disk_gb_enabled

  # Check if all shards have the same region topology
  # The comparison varies based on auto-scaling settings:
  # - With compute auto-scaling: ignore instance_size (it varies)
  # - With disk auto-scaling: ignore disk_size_gb (it varies)
  # - Without auto-scaling: check everything
  all_shards_same_topology = local.is_sharded ? (
    length(distinct([
      for spec in local.cluster.replication_specs :
      # Create a signature for each shard's configuration
      join("|", sort([
        for rc in spec.region_configs :
        format("%s:%d:%d:%d%s%s%s%s",
          # Always check: region name and node counts
          rc.region_name,
          rc.electable_specs.node_count,
          rc.read_only_specs.node_count,
          rc.analytics_specs.node_count,
          # Instance sizes: only check if compute auto-scaling is disabled
          local.auto_scaling_compute_enabled ? "" : format(":%s:%s",
            rc.electable_specs.instance_size,
            rc.analytics_specs.instance_size
          ),
          # Disk size: only check if disk auto-scaling is disabled
          local.auto_scaling_disk_enabled ? "" : format(":%s", rc.electable_specs.disk_size_gb),
          # Disk IOPS: only check if not using PROVISIONED or if needed
          rc.electable_specs.ebs_volume_type == "PROVISIONED" ? format(":%s", rc.electable_specs.disk_iops) : "",
          # EBS volume type: always check
          format(":%s", rc.electable_specs.ebs_volume_type),
        )
      ]))
    ])) == 1
  ) : false

  # Use shard_count only if all shards have identical topology
  use_shard_count = local.all_shards_same_topology

  # For uniform sharded clusters, only include regions from the first shard
  # For non-uniform sharded clusters, include all regions
  regions_to_use = local.all_shards_same_topology ? [
    for region in local.all_regions_with_shard_info : region if region.shard_number == 0
  ] : local.all_regions_with_shard_info

  # Extract common values across all regions BEFORE transforming them
  # Only set a value as "common" if ALL regions have the same value
  common_provider_name = length(distinct([for r in local.all_regions_with_shard_info : r.provider_name])) == 1 ? local.all_regions_with_shard_info[0].provider_name : null

  # Get instance size - only common if ALL electable regions have the same value (and not using autoscaling)
  first_electable_region = [for r in local.all_regions_with_shard_info : r if r.node_count > 0][0]
  electable_regions      = [for r in local.all_regions_with_shard_info : r if r.node_count > 0]
  common_instance_size = (
    !local.auto_scaling_compute_enabled &&
    length(distinct([for r in local.electable_regions : r.instance_size])) == 1
  ) ? local.first_electable_region.instance_size : null

  # Get disk configuration - only common if ALL electable regions have the same values
  common_disk_size_gb = (
    !local.auto_scaling_disk_enabled &&
    length(distinct([for r in local.electable_regions : r.disk_size_gb])) == 1
  ) ? local.first_electable_region.disk_size_gb : null

  common_ebs_volume_type = (
    length(distinct([for r in local.electable_regions : r.ebs_volume_type])) == 1 &&
    local.first_electable_region.ebs_volume_type == "PROVISIONED"
  ) ? "PROVISIONED" : null

  common_disk_iops = (
    local.common_ebs_volume_type == "PROVISIONED" &&
    length(distinct([for r in local.electable_regions : r.disk_iops])) == 1 &&
    local.first_electable_region.disk_iops > 0
  ) ? local.first_electable_region.disk_iops : null

  # Get analytics instance size - only common if ALL analytics regions have the same value
  analytics_regions      = [for r in local.all_regions_with_shard_info : r if r.node_count_analytics > 0]
  first_analytics_region = length(local.analytics_regions) > 0 ? local.analytics_regions[0] : null
  common_instance_size_analytics = (
    local.first_analytics_region != null &&
    !local.auto_scaling_compute_analytics_enabled &&
    length(distinct([for r in local.analytics_regions : r.instance_size_analytics])) == 1
  ) ? local.first_analytics_region.instance_size_analytics : null

  # For REPLICASET, remove shard_number (set to null)
  # For SHARDED, keep shard_number but remove zone_name
  # For GEOSHARDED, keep both zone_name and optionally shard_number
  # Also: exclude fields from regions if they're set at root level as common values
  regions_transformed = [
    for region in local.regions_to_use : {
      name = region.name
      # Only include provider_name in region if there's no common provider_name
      provider_name        = local.common_provider_name == null ? region.provider_name : null
      node_count           = region.node_count > 0 ? region.node_count : null
      node_count_read_only = region.node_count_read_only > 0 ? region.node_count_read_only : null
      node_count_analytics = region.node_count_analytics > 0 ? region.node_count_analytics : null
      # Only include instance_size if not using compute auto-scaling AND not set at root level
      instance_size = (
        region.instance_size != "" && !local.auto_scaling_compute_enabled &&
        local.common_instance_size == null
      ) ? region.instance_size : null
      # Only include instance_size_analytics if not using analytics auto-scaling AND not set at root level
      instance_size_analytics = (
        region.node_count_analytics > 0 && region.instance_size_analytics != "" &&
        !local.auto_scaling_compute_analytics_enabled &&
        local.common_instance_size_analytics == null
      ) ? region.instance_size_analytics : null
      # Only include disk_size_gb if not using disk auto-scaling AND not set at root level
      disk_size_gb = (
        !region.auto_scaling.disk_gb_enabled && region.disk_size_gb > 0 &&
        local.common_disk_size_gb == null
      ) ? region.disk_size_gb : null
      # Only include disk_iops if using PROVISIONED volumes AND not set at root level
      disk_iops = (
        region.ebs_volume_type == "PROVISIONED" && region.disk_iops > 0 &&
        local.common_disk_iops == null
      ) ? region.disk_iops : null
      # Only include ebs_volume_type if PROVISIONED AND not set at root level
      ebs_volume_type = (
        region.ebs_volume_type == "PROVISIONED" &&
        local.common_ebs_volume_type == null
      ) ? "PROVISIONED" : null
      shard_number = local.is_replicaset || local.all_shards_same_topology ? null : region.shard_number
      zone_name    = local.is_geosharded ? region.zone_name : null
    }
  ]


  # Check if auto_scaling matches defaults
  auto_scaling_is_default = (
    local.auto_scaling_raw.compute_enabled == local.module_defaults.auto_scaling.compute_enabled &&
    (local.auto_scaling_raw.compute_max_instance_size == local.module_defaults.auto_scaling.compute_max_instance_size || local.auto_scaling_raw.compute_max_instance_size == "") &&
    (local.auto_scaling_raw.compute_min_instance_size == local.module_defaults.auto_scaling.compute_min_instance_size || local.auto_scaling_raw.compute_min_instance_size == "") &&
    local.auto_scaling_raw.compute_scale_down_enabled == local.module_defaults.auto_scaling.compute_scale_down_enabled &&
    local.auto_scaling_raw.disk_gb_enabled == local.module_defaults.auto_scaling.disk_gb_enabled
  )

  # Only output auto_scaling if it differs from defaults
  auto_scaling = local.auto_scaling_is_default ? null : {
    compute_enabled            = local.auto_scaling_raw.compute_enabled
    compute_max_instance_size  = local.auto_scaling_raw.compute_max_instance_size != "" ? local.auto_scaling_raw.compute_max_instance_size : null
    compute_min_instance_size  = local.auto_scaling_raw.compute_min_instance_size != "" ? local.auto_scaling_raw.compute_min_instance_size : null
    compute_scale_down_enabled = local.auto_scaling_raw.compute_scale_down_enabled
    disk_gb_enabled            = local.auto_scaling_raw.disk_gb_enabled
  }

  # Filter advanced_configuration to only include non-default values
  advanced_configuration_filtered = {
    change_stream_options_pre_and_post_images_expire_after_seconds = local.cluster.advanced_configuration.change_stream_options_pre_and_post_images_expire_after_seconds != -1 ? local.cluster.advanced_configuration.change_stream_options_pre_and_post_images_expire_after_seconds : null
    custom_openssl_cipher_config_tls12                             = length(local.cluster.advanced_configuration.custom_openssl_cipher_config_tls12) > 0 ? tolist(local.cluster.advanced_configuration.custom_openssl_cipher_config_tls12) : null
    default_max_time_ms                                            = local.cluster.advanced_configuration.default_max_time_ms
    default_write_concern                                          = local.cluster.advanced_configuration.default_write_concern != local.module_defaults.advanced_configuration.default_write_concern && local.cluster.advanced_configuration.default_write_concern != "" ? local.cluster.advanced_configuration.default_write_concern : null
    javascript_enabled                                             = local.cluster.advanced_configuration.javascript_enabled != local.module_defaults.advanced_configuration.javascript_enabled ? local.cluster.advanced_configuration.javascript_enabled : null
    minimum_enabled_tls_protocol                                   = local.cluster.advanced_configuration.minimum_enabled_tls_protocol != local.module_defaults.advanced_configuration.minimum_enabled_tls_protocol ? local.cluster.advanced_configuration.minimum_enabled_tls_protocol : null
    no_table_scan                                                  = local.cluster.advanced_configuration.no_table_scan ? local.cluster.advanced_configuration.no_table_scan : null
    oplog_min_retention_hours                                      = local.cluster.advanced_configuration.oplog_min_retention_hours > 0 ? local.cluster.advanced_configuration.oplog_min_retention_hours : null
    oplog_size_mb                                                  = local.cluster.advanced_configuration.oplog_size_mb > 0 ? local.cluster.advanced_configuration.oplog_size_mb : null
    sample_refresh_interval_bi_connector                           = local.cluster.advanced_configuration.sample_refresh_interval_bi_connector > 0 ? local.cluster.advanced_configuration.sample_refresh_interval_bi_connector : null
    sample_size_bi_connector                                       = local.cluster.advanced_configuration.sample_size_bi_connector > 0 ? local.cluster.advanced_configuration.sample_size_bi_connector : null
    tls_cipher_config_mode                                         = local.cluster.advanced_configuration.tls_cipher_config_mode != "DEFAULT" && local.cluster.advanced_configuration.tls_cipher_config_mode != "" ? local.cluster.advanced_configuration.tls_cipher_config_mode : null
    transaction_lifetime_limit_seconds                             = local.cluster.advanced_configuration.transaction_lifetime_limit_seconds > 0 ? local.cluster.advanced_configuration.transaction_lifetime_limit_seconds : null
  }

  # Check if advanced_configuration has any non-null values
  advanced_configuration_has_values = anytrue([
    for k, v in local.advanced_configuration_filtered : v != null
  ])

  # Determine output filename
  output_filename = coalesce(var.filename, "cluster_${local.cluster.name}")

  # Format regions list - only include non-null values
  regions_hcl = join("", [
    for region in local.regions_transformed :
    <<-EOT
    {
      name          = ${format("%q", region.name)}${region.provider_name != null ? format("\n      provider_name = %q", region.provider_name) : ""}${region.node_count != null ? format("\n      node_count    = %v", region.node_count) : ""}${region.node_count_read_only != null ? format("\n      node_count_read_only = %v", region.node_count_read_only) : ""}${region.node_count_analytics != null ? format("\n      node_count_analytics = %v", region.node_count_analytics) : ""}${region.instance_size != null ? format("\n      instance_size = %q", region.instance_size) : ""}${region.instance_size_analytics != null ? format("\n      instance_size_analytics = %q", region.instance_size_analytics) : ""}${region.disk_size_gb != null ? format("\n      disk_size_gb  = %v", region.disk_size_gb) : ""}${region.disk_iops != null ? format("\n      disk_iops     = %v", region.disk_iops) : ""}${region.ebs_volume_type != null ? format("\n      ebs_volume_type = %q", region.ebs_volume_type) : ""}${region.shard_number != null ? format("\n      shard_number  = %v", region.shard_number) : ""}${region.zone_name != null ? format("\n      zone_name     = %q", region.zone_name) : ""}
    },
    EOT
  ])

  # Format auto_scaling block as proper HCL
  auto_scaling_hcl = local.auto_scaling != null ? "\n\n  auto_scaling = {\n    compute_enabled            = ${local.auto_scaling.compute_enabled}${local.auto_scaling.compute_max_instance_size != null ? format("\n    compute_max_instance_size  = %q", local.auto_scaling.compute_max_instance_size) : ""}${local.auto_scaling.compute_min_instance_size != null ? format("\n    compute_min_instance_size  = %q", local.auto_scaling.compute_min_instance_size) : ""}\n    compute_scale_down_enabled = ${local.auto_scaling.compute_scale_down_enabled}\n    disk_gb_enabled            = ${local.auto_scaling.disk_gb_enabled}\n  }" : ""

  # Format auto_scaling_analytics block as proper HCL
  auto_scaling_analytics_hcl = local.analytics_auto_scaling != null ? "\n\n  auto_scaling_analytics = {\n    compute_enabled            = ${local.analytics_auto_scaling.compute_enabled}${local.analytics_auto_scaling.compute_max_instance_size != null ? format("\n    compute_max_instance_size  = %q", local.analytics_auto_scaling.compute_max_instance_size) : ""}${local.analytics_auto_scaling.compute_min_instance_size != null ? format("\n    compute_min_instance_size  = %q", local.analytics_auto_scaling.compute_min_instance_size) : ""}\n    compute_scale_down_enabled = ${local.analytics_auto_scaling.compute_scale_down_enabled}\n    disk_gb_enabled            = ${local.analytics_auto_scaling.disk_gb_enabled}\n  }" : ""

  module_instance_name = replace(local.cluster.name, "-", "_")

  # Build optional module attributes
  module_optional_attributes = join("", compact(concat(
    [format("\n  retain_backups_enabled = null # Retain backups after cluster deletion")],
    [local.common_provider_name != null ? format("\n  provider_name = %q", local.common_provider_name) : ""],
    [local.common_instance_size != null ? format("\n  instance_size = %q", local.common_instance_size) : ""],
    [local.common_disk_size_gb != null ? format("\n  disk_size_gb  = %v", local.common_disk_size_gb) : ""],
    [local.common_disk_iops != null ? format("\n  disk_iops     = %v", local.common_disk_iops) : ""],
    [local.common_ebs_volume_type != null ? format("\n  ebs_volume_type = %q", local.common_ebs_volume_type) : ""],
    [local.common_instance_size_analytics != null ? format("\n  instance_size_analytics = %q", local.common_instance_size_analytics) : ""],
    [local.use_shard_count && local.shard_count != null ? format("\n  shard_count = %v", local.shard_count) : ""],
    [local.cluster.mongo_db_major_version != "" ? format("\n  mongo_db_major_version = %q", local.cluster.mongo_db_major_version) : ""],
    [local.cluster.backup_enabled != true ? format("\n  backup_enabled = %v", local.cluster.backup_enabled) : ""],
    [local.cluster.pit_enabled != true ? format("\n  pit_enabled = %v", local.cluster.pit_enabled) : ""],
    [local.cluster.termination_protection_enabled ? format("\n  termination_protection_enabled = %v", local.cluster.termination_protection_enabled) : ""],
    [local.cluster.redact_client_log_data != true ? format("\n  redact_client_log_data = %v", local.cluster.redact_client_log_data) : ""],
    [local.cluster.encryption_at_rest_provider != "NONE" && local.cluster.encryption_at_rest_provider != "" ? format("\n  encryption_at_rest_provider = %q", local.cluster.encryption_at_rest_provider) : ""],
    [local.cluster.version_release_system != "" && local.cluster.version_release_system != "LTS" ? format("\n  version_release_system = %q", local.cluster.version_release_system) : ""],
    [local.cluster.replica_set_scaling_strategy != "" ? format("\n  replica_set_scaling_strategy = %q", local.cluster.replica_set_scaling_strategy) : ""],
    [local.cluster.global_cluster_self_managed_sharding ? format("\n  global_cluster_self_managed_sharding = %v", local.cluster.global_cluster_self_managed_sharding) : ""],
    [length(local.cluster.tags) > 0 ? format("\n  tags = %s", jsonencode(local.cluster.tags)) : ""],
    [length(local.cluster.tags) == 0 ? format("\n  tags = null") : ""],
    [local.auto_scaling_hcl],
    [local.auto_scaling_analytics_hcl],
    [local.advanced_configuration_has_values ? format("\n\n  advanced_configuration = %s", jsonencode(local.advanced_configuration_filtered)) : ""],
    [local.cluster.bi_connector_config.enabled ? format("\n\n  bi_connector_config = %s", jsonencode({ enabled = local.cluster.bi_connector_config.enabled, read_preference = local.cluster.bi_connector_config.read_preference })) : ""]
  )))

  # Generate the complete .tf file content
  terraform_file_content = <<-EOT
# Auto-generated from existing cluster: ${local.cluster.name}
# Cluster Type: ${local.cluster_type}
# Generated: ${timestamp()}

import {
  id = "$${var.project_id}-${local.cluster.name}"
  to = module.${local.module_instance_name}.mongodbatlas_advanced_cluster.this
}

module "${local.module_instance_name}" {
  source = "../../../"  # Adjust path to your cluster module

  project_id = var.project_id
  name = ${format("%q", local.cluster.name)}
  cluster_type = ${format("%q", local.cluster_type)}

  regions = [
${local.regions_hcl}  ]
${local.module_optional_attributes}
}

# Outputs
output "${local.module_instance_name}_connection_strings" {
  description = "Connection strings for ${local.cluster.name}"
  value       = module.${local.module_instance_name}.connection_strings
}
EOT
  filepath               = "${var.output_directory}/${local.output_filename}.tf"
}

# Write the generated terraform file
resource "local_file" "cluster_config" {
  content  = local.terraform_file_content
  filename = local.filepath
}
