
locals {
  DEFAULT_INSTANCE_SIZE = "M10" # TODO: Suggestion to add warnings / errors conditional to the environment tag. If `environment` is production an error should raise if instance_size = M0 is set, and linked to Architecture Center.

  regions = coalesce(var.regions, [])

  is_geosharded = length(local.regions) > 0 && alltrue([for r in local.regions : r.zone_name != null])
  is_sharded    = length(local.regions) > 0 && alltrue([for r in local.regions : r.shard_index != null])

  computed_cluster_type = var.cluster_type != null ? var.cluster_type : (
    local.is_geosharded ? "GEOSHARDED" : (local.is_sharded ? "SHARDED" : "REPLICASET")
  )

  unique_zone_names    = local.computed_cluster_type == "GEOSHARDED" ? sort(distinct([for r in local.regions : r.zone_name if r.zone_name != null])) : []
  unique_shard_indices = local.computed_cluster_type == "SHARDED" ? sort(distinct([for r in local.regions : r.shard_index if r.shard_index != null])) : []
  # list of lists of regions, grouped by cluster type
  cluster_type_regions = {
    REPLICASET = [local.regions]
    # unique_shard_indices is a list of strings, so we need to use _ to ignore the value otherwise the comparision will not work leaving empty lists
    SHARDED    = [for idx, _ in local.unique_shard_indices : [for r in local.regions : r if r.shard_index == idx]]
    GEOSHARDED = [for z in local.unique_zone_names : [for r in local.regions : r if r.zone_name == z]]
  }

  grouped_regions = local.cluster_type_regions[local.computed_cluster_type]

  auto_scaling_compute = var.auto_scaling.compute_enabled
  auto_scaling_compute_analytics = var.auto_scaling_analytics == null ? false : var.auto_scaling_analytics.compute_enabled

effective_auto_scaling = local.auto_scaling_compute ? var.auto_scaling : {
  for k, v in var.auto_scaling :
  k => v if !contains([
    "compute_max_instance_size",
    "compute_min_instance_size",
    "compute_scale_down_enabled"
  ], k)
}

effective_auto_scaling_analytics = var.auto_scaling_analytics == null ? null : (
  local.auto_scaling_compute_analytics ? var.auto_scaling_analytics : {
    for k, v in var.auto_scaling_analytics :
    k => v if !contains([
      "compute_max_instance_size",
      "compute_min_instance_size",
      "compute_scale_down_enabled"
    ], k)
  })

  // Build replication_specs matching the provider schema
  replication_specs_built = tolist([
    for shard_index, region_group in local.grouped_regions : {
      zone_name = local.computed_cluster_type == "GEOSHARDED" ? region_group[0].zone_name : null
      region_configs = tolist([
        for region_index, r in region_group : {
          provider_name          = r.provider_name != null ? r.provider_name : var.provider_name
          region_name            = r.name
          priority               = 7 - region_index # TODO: Ensure it doesn't become negative for > 8 regions. Validate how this is handled.
          auto_scaling           = local.effective_auto_scaling
          analytics_auto_scaling = local.effective_auto_scaling_analytics
          electable_specs = r.node_count != null ? {
            disk_size_gb = var.disk_size_gb
            instance_size = local.effective_auto_scaling.compute_enabled ? try(
              local.existing_cluster.old_cluster.replication_specs[shard_index].region_configs[region_index].electable_specs.instance_size,
              local.effective_auto_scaling.compute_min_instance_size
            ) : coalesce(r.instance_size, var.instance_size, local.DEFAULT_INSTANCE_SIZE)
            node_count = r.node_count
          } : null
          read_only_specs = r.node_count_read_only != null ? {
            disk_size_gb = var.disk_size_gb
            instance_size = local.effective_auto_scaling.compute_enabled ? try(
              local.existing_cluster.old_cluster.replication_specs[shard_index].region_configs[region_index].read_only_specs.instance_size,
              local.effective_auto_scaling.compute_min_instance_size
            ) : coalesce(r.instance_size, var.instance_size, local.DEFAULT_INSTANCE_SIZE)
            node_count = r.node_count_read_only
          } : null
          analytics_specs = r.node_count_analytics != null ? {
            disk_size_gb = var.disk_size_gb
            instance_size = (local.effective_auto_scaling_analytics != null && local.effective_auto_scaling_analytics.compute_enabled) ? try(
              local.existing_cluster.old_cluster.replication_specs[shard_index].region_configs[region_index].analytics_specs.instance_size,
              local.effective_auto_scaling_analytics.compute_min_instance_size
            ) : coalesce(r.instance_size_analytics, var.instance_size_analytics, local.DEFAULT_INSTANCE_SIZE)
            node_count = r.node_count_analytics
          } : null
        }
      ])
    }
  ])
  replication_specs_resource_var_used = length(var.replication_specs) > 0
  replication_specs_json              = local.replication_specs_resource_var_used ? jsonencode(var.replication_specs) : jsonencode(local.replication_specs_built) # avoids "Mismatched list element types"
  empty_region_configs                = local.replication_specs_resource_var_used ? [] : [for idx, r in local.replication_specs_built : "replication_specs[${idx}].region_configs is empty" if length(r.region_configs) == 0]
  empty_regions                       = length(local.regions) == 0

  // Validation messages (non-empty strings represent errors)
  validation_errors = compact(concat(
    local.empty_region_configs,

    // Mutual exclusivity
    length(var.regions) > 0 && local.replication_specs_resource_var_used ? ["Cannot use var.regions and var.replication_specs together, set regions=[] to use var.replication_specs"] : [],
    var.auto_scaling.compute_enabled && var.instance_size != null ? ["Cannot set var.instance_size when auto_scaling is enabled. Set auto_scaling.compute_enabled=false to use fixed instance sizes"] : [],
    var.auto_scaling_analytics != null && var.instance_size_analytics != null ? ["Cannot use var.auto_scaling_analytics and var.instance_size_analytics together"] : [],

    // Requires
    var.instance_size != null && local.empty_regions && !local.replication_specs_resource_var_used ? ["Cannot use var.instance_size without var.regions"] : [],
    var.auto_scaling != null && local.empty_regions && !local.replication_specs_resource_var_used ? ["Cannot use var.auto_scaling without var.regions"] : [],
    var.auto_scaling_analytics != null && local.empty_regions && !local.replication_specs_resource_var_used ? ["Cannot use var.auto_scaling_analytics without var.regions"] : [],

    // Per-region invalid instance_size when autoscaling is used
    var.auto_scaling.compute_enabled ? [for idx, r in local.regions : r.instance_size != null ? "Cannot use regions[*].instance_size when auto_scaling is enabled: index ${idx} instance_size=${r.instance_size}" : ""] : [],
    var.auto_scaling_analytics != null ? [for idx, r in local.regions : r.instance_size_analytics != null ? "Cannot use regions[*].instance_size_analytics when auto_scaling_analytics is used: index ${idx} instance_size_analytics=${r.instance_size_analytics}" : ""] : [],

    // Cluster type vs region fields
    local.computed_cluster_type == "GEOSHARDED" ? concat(
      [for idx, r in local.regions : r.zone_name == null ? "Must use regions[*].zone_name when cluster_type is GEOSHARDED: zone_name missing @ index ${idx}" : ""],
      [for idx, r in local.regions : r.shard_index != null ? "Geosharded cluster should not define shard_index: regions[${idx}].shard_index=${r.shard_index}" : ""]
    ) : [],
    local.computed_cluster_type == "SHARDED" ? concat(
      [for idx, r in local.regions : r.shard_index == null ? "Must use regions[*].shard_index when cluster_type is SHARDED: shard_index missing @ index ${idx}" : ""],
      [for idx, r in local.regions : r.zone_name != null ? "Sharded cluster should not define zone_name: regions[${idx}].zone_name=${r.zone_name}" : ""]
    ) : [],
    local.computed_cluster_type == "REPLICASET" ? concat(
      [for idx, r in local.regions : r.shard_index != null ? "Replicaset cluster should not define shard_index: regions[${idx}].shard_index=${r.shard_index}" : ""],
      [for idx, r in local.regions : r.zone_name != null ? "Replicaset cluster should not define zone_name: regions[${idx}].zone_name=${r.zone_name}" : ""]
    ) : [],

    // Provider name presence
    var.provider_name == null ? [for idx, r in local.regions : r.provider_name == null ? "Must use regions[*].provider_name when root provider_name is not specified: regions[${idx}].provider_name is missing" : ""] : []
  ))
}


resource "mongodbatlas_advanced_cluster" "this" {
  lifecycle {
    precondition {
      condition     = length(local.validation_errors) == 0
      error_message = join("\n", local.validation_errors)
    }
  }

  cluster_type                                     = local.computed_cluster_type
  name                                             = var.name
  project_id                                       = var.project_id
  replication_specs                                = jsondecode(local.replication_specs_json)
  accept_data_risks_and_force_replica_set_reconfig = var.accept_data_risks_and_force_replica_set_reconfig
  advanced_configuration                           = var.advanced_configuration
  backup_enabled                                   = var.backup_enabled
  bi_connector_config                              = var.bi_connector_config
  config_server_management_mode                    = var.config_server_management_mode
  delete_on_create_timeout                         = var.delete_on_create_timeout
  encryption_at_rest_provider                      = var.encryption_at_rest_provider
  global_cluster_self_managed_sharding             = var.global_cluster_self_managed_sharding
  mongo_db_major_version                           = var.mongo_db_major_version
  paused                                           = var.paused
  pinned_fcv                                       = var.pinned_fcv
  pit_enabled                                      = var.pit_enabled
  redact_client_log_data                           = var.redact_client_log_data
  replica_set_scaling_strategy                     = var.replica_set_scaling_strategy
  retain_backups_enabled                           = var.retain_backups_enabled
  root_cert_type                                   = var.root_cert_type
  tags                                             = var.tags
  termination_protection_enabled                   = var.termination_protection_enabled
  timeouts                                         = var.timeouts
  version_release_system                           = var.version_release_system
}
