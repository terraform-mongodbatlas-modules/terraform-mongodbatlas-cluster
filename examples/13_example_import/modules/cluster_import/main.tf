locals {
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
    for shard_idx, spec in var.cluster.replication_specs : [
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
  cluster_type  = var.cluster.cluster_type
  is_replicaset = local.cluster_type == "REPLICASET"
  is_sharded    = local.cluster_type == "SHARDED"
  is_geosharded = local.cluster_type == "GEOSHARDED"

  # For REPLICASET, remove shard_number (set to null)
  # For SHARDED, keep shard_number but remove zone_name
  # For GEOSHARDED, keep both zone_name and optionally shard_number
  regions_transformed = [
    for region in local.all_regions_with_shard_info : {
      name                    = region.name
      provider_name           = region.provider_name
      node_count              = region.node_count > 0 ? region.node_count : null
      node_count_read_only    = region.node_count_read_only > 0 ? region.node_count_read_only : null
      node_count_analytics    = region.node_count_analytics > 0 ? region.node_count_analytics : null
      instance_size           = region.instance_size != "" ? region.instance_size : null
      instance_size_analytics = region.node_count_analytics > 0 && region.instance_size_analytics != "" ? region.instance_size_analytics : null
      # Don't include disk_size_gb if disk auto-scaling is enabled
      disk_size_gb    = !region.auto_scaling.disk_gb_enabled && region.disk_size_gb > 0 ? region.disk_size_gb : null
      # Only include disk_iops and ebs_volume_type if ebs_volume_type is PROVISIONED
      disk_iops       = region.ebs_volume_type == "PROVISIONED" && region.disk_iops > 0 ? region.disk_iops : null
      ebs_volume_type = region.ebs_volume_type == "PROVISIONED" ? "PROVISIONED" : null
      shard_number    = local.is_replicaset ? null : region.shard_number
      zone_name       = local.is_geosharded ? region.zone_name : null
    }
  ]

  # Extract common values across all regions
  common_provider_name = length(distinct([for r in local.all_regions_with_shard_info : r.provider_name])) == 1 ? local.all_regions_with_shard_info[0].provider_name : null

  # Get instance size from first electable region (if not using autoscaling)
  first_electable_region = [for r in local.all_regions_with_shard_info : r if r.node_count > 0][0]
  common_instance_size   = local.first_electable_region.auto_scaling.compute_enabled ? null : local.first_electable_region.instance_size

  # Get disk configuration from first electable region
  # Don't include disk_size_gb if disk auto-scaling is enabled
  common_disk_size_gb = !local.first_electable_region.auto_scaling.disk_gb_enabled ? local.first_electable_region.disk_size_gb : null
  # Only include disk_iops and ebs_volume_type if ebs_volume_type is PROVISIONED
  common_ebs_volume_type = local.first_electable_region.ebs_volume_type == "PROVISIONED" ? "PROVISIONED" : null
  common_disk_iops       = local.first_electable_region.ebs_volume_type == "PROVISIONED" && local.first_electable_region.disk_iops > 0 ? local.first_electable_region.disk_iops : null

  # Get analytics instance size from first analytics region (if any)
  first_analytics_region         = length([for r in local.all_regions_with_shard_info : r if r.node_count_analytics > 0]) > 0 ? [for r in local.all_regions_with_shard_info : r if r.node_count_analytics > 0][0] : null
  common_instance_size_analytics = local.first_analytics_region != null && (local.first_analytics_region.analytics_auto_scaling == null || !local.first_analytics_region.analytics_auto_scaling.compute_enabled) ? local.first_analytics_region.instance_size_analytics : null

  # Auto scaling configuration from first region
  auto_scaling_raw       = local.first_electable_region.auto_scaling
  analytics_auto_scaling = local.first_analytics_region != null ? local.first_analytics_region.analytics_auto_scaling : null

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

  # Determine shard_count for SHARDED clusters (if all shards have same topology)
  shard_count = local.is_sharded ? length(var.cluster.replication_specs) : null

  # Check if all shards have the same region topology
  all_shards_same_topology = local.is_sharded ? (
    length(distinct([
      for spec in var.cluster.replication_specs :
      join(",", sort([for rc in spec.region_configs : rc.region_name]))
    ])) == 1
  ) : false

  # Use shard_count only if all shards have identical topology
  use_shard_count = local.all_shards_same_topology

  # Filter advanced_configuration to only include non-default values
  advanced_configuration_filtered = {
    change_stream_options_pre_and_post_images_expire_after_seconds = var.cluster.advanced_configuration.change_stream_options_pre_and_post_images_expire_after_seconds != -1 ? var.cluster.advanced_configuration.change_stream_options_pre_and_post_images_expire_after_seconds : null
    custom_openssl_cipher_config_tls12                             = length(var.cluster.advanced_configuration.custom_openssl_cipher_config_tls12) > 0 ? tolist(var.cluster.advanced_configuration.custom_openssl_cipher_config_tls12) : null
    default_max_time_ms                                            = var.cluster.advanced_configuration.default_max_time_ms
    default_write_concern                                          = var.cluster.advanced_configuration.default_write_concern != local.module_defaults.advanced_configuration.default_write_concern && var.cluster.advanced_configuration.default_write_concern != "" ? var.cluster.advanced_configuration.default_write_concern : null
    javascript_enabled                                             = var.cluster.advanced_configuration.javascript_enabled != local.module_defaults.advanced_configuration.javascript_enabled ? var.cluster.advanced_configuration.javascript_enabled : null
    minimum_enabled_tls_protocol                                   = var.cluster.advanced_configuration.minimum_enabled_tls_protocol != local.module_defaults.advanced_configuration.minimum_enabled_tls_protocol ? var.cluster.advanced_configuration.minimum_enabled_tls_protocol : null
    no_table_scan                                                  = var.cluster.advanced_configuration.no_table_scan ? var.cluster.advanced_configuration.no_table_scan : null
    oplog_min_retention_hours                                      = var.cluster.advanced_configuration.oplog_min_retention_hours > 0 ? var.cluster.advanced_configuration.oplog_min_retention_hours : null
    oplog_size_mb                                                  = var.cluster.advanced_configuration.oplog_size_mb > 0 ? var.cluster.advanced_configuration.oplog_size_mb : null
    sample_refresh_interval_bi_connector                           = var.cluster.advanced_configuration.sample_refresh_interval_bi_connector > 0 ? var.cluster.advanced_configuration.sample_refresh_interval_bi_connector : null
    sample_size_bi_connector                                       = var.cluster.advanced_configuration.sample_size_bi_connector > 0 ? var.cluster.advanced_configuration.sample_size_bi_connector : null
    tls_cipher_config_mode                                         = var.cluster.advanced_configuration.tls_cipher_config_mode != "DEFAULT" && var.cluster.advanced_configuration.tls_cipher_config_mode != "" ? var.cluster.advanced_configuration.tls_cipher_config_mode : null
    transaction_lifetime_limit_seconds                             = var.cluster.advanced_configuration.transaction_lifetime_limit_seconds > 0 ? var.cluster.advanced_configuration.transaction_lifetime_limit_seconds : null
  }

  # Check if advanced_configuration has any non-null values
  advanced_configuration_has_values = anytrue([
    for k, v in local.advanced_configuration_filtered : v != null
  ])
}
