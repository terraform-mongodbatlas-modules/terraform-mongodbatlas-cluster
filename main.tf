locals {
  DEFAULT_INSTANCE_SIZE = "M10"

  regions = coalesce(var.regions, [])

  is_geosharded                       = var.cluster_type == "GEOSHARDED"
  is_sharded                          = var.cluster_type == "SHARDED"
  is_replicaset                       = var.cluster_type == "REPLICASET"
  replication_specs_resource_var_used = length(var.replication_specs) > 0

  # ---- REPLICASET  ----
  grouped_regions_replicaset = local.is_replicaset ? [local.regions] : []

  # ---- SHARDED  ----
  sharded_uniform          = local.is_sharded && var.shard_count != null
  sharded_explicit         = local.is_sharded && var.shard_count == null
  has_any_zone_in_shard    = local.is_sharded && anytrue([for r in var.regions : r.zone_name != null && trimspace(r.zone_name) != ""])
  has_any_number_in_shard  = local.is_sharded && anytrue([for r in var.regions : r.shard_number != null])
  all_have_number_in_shard = local.is_sharded && length(var.regions) > 0 && alltrue([for r in var.regions : r.shard_number != null])
  sharded_validation_errors = local.is_sharded && !local.replication_specs_resource_var_used ? compact(concat(
    local.has_any_zone_in_shard
    ? ["SHARDED validation: do not set regions[*].zone_name."] : [],

    (local.sharded_uniform && local.has_any_number_in_shard)
    ? ["SHARDED validation: when shard_count is set, do not set regions[*].shard_number."] : [],

    (!local.sharded_uniform && !local.all_have_number_in_shard)
    ? ["SHARDED validation: set regions[*].shard_number on every region (or use shard_count)."] : [],

    (local.sharded_uniform && length(var.regions) == 0)
    ? ["SHARDED: when shard_count is set, you must define at least one region."] : []
  )) : []

  unique_shard_numbers = local.sharded_explicit ? distinct([
    for r in local.regions : tostring(r.shard_number)
    if r.shard_number != null
  ]) : []

  grouped_regions_sharded_explicit = local.sharded_explicit ? [
    for sn in local.unique_shard_numbers :
    [for r in local.regions : r if tostring(r.shard_number) == sn]
  ] : []

  grouped_regions_sharded_uniform = local.sharded_uniform ? [
    for _i in range(var.shard_count) : local.regions
  ] : []

  # ---- GEOSHARDED  ----
  geo_rows = local.is_geosharded ? [
    for r in local.regions : r
    if r.zone_name != null && trimspace(r.zone_name) != ""
  ] : []

  unique_zone_names = local.is_geosharded ? distinct([
    for r in local.geo_rows : trimspace(r.zone_name)
  ]) : []

  # per-zone counts to ensure either "all-or-none" region blocks within each zone have shard_number set.
  # if no regions in a zone have shard_number set, then they are all assigned to the one shard by default.
  zones_with_counts = local.is_geosharded ? {
    for z in local.unique_zone_names :
    z => {
      with_sn    = length([for r in local.geo_rows : r if trimspace(r.zone_name) == z && r.shard_number != null])
      without_sn = length([for r in local.geo_rows : r if trimspace(r.zone_name) == z && r.shard_number == null])
    }
  } : {}

  invalid_geo_zones_mixed = local.is_geosharded ? [
    for z, c in local.zones_with_counts :
    z if(c.with_sn > 0 && c.without_sn > 0)
  ] : []

  zones_numbered = local.is_geosharded ? {
    for z, c in local.zones_with_counts : z => (c.with_sn > 0 && c.without_sn == 0)
  } : {}

  # compute a key per region block:
  #  - numbered zone: "zone||<shard_number>"
  #  - single-shard zone: "zone||0"
  geo_keyed_rows = local.is_geosharded ? [
    for r in local.geo_rows : {
      key    = local.zones_numbered[trimspace(r.zone_name)] ? "${trimspace(r.zone_name)}||${format("%09d", r.shard_number)}" : "${trimspace(r.zone_name)}||000000000"
      region = r
    }
  ] : []

  geoshard_keys = local.is_geosharded ? distinct([
    for x in local.geo_keyed_rows : x.key
  ]) : []

  # group by computed key: "zone||<shard_number>"
  grouped_regions_geosharded = local.is_geosharded ? [
    for key in local.geoshard_keys : [
      for x in local.geo_keyed_rows : x.region if x.key == key
    ]
  ] : []
  cluster_type_regions = {
    REPLICASET = local.grouped_regions_replicaset
    SHARDED    = local.sharded_uniform ? local.grouped_regions_sharded_uniform : local.grouped_regions_sharded_explicit
    GEOSHARDED = local.grouped_regions_geosharded
  }

  grouped_regions = local.cluster_type_regions[var.cluster_type]

  auto_scaling_compute_enabled           = var.auto_scaling.compute_enabled
  auto_scaling_disk_enabled              = var.auto_scaling.disk_gb_enabled
  auto_scaling_compute_enabled_analytics = var.auto_scaling_analytics == null ? false : var.auto_scaling_analytics.compute_enabled
  manual_compute_analytics               = var.instance_size_analytics != null || length([for idx, r in local.regions : idx if r.instance_size_analytics != null]) > 0
  manual_compute_electable               = var.instance_size != null || length([for idx, r in local.regions : idx if r.instance_size != null]) > 0
  manual_compute                         = local.manual_compute_electable || local.manual_compute_analytics

  effective_auto_scaling = local.auto_scaling_compute_enabled ? var.auto_scaling : {
    for k, v in var.auto_scaling :
    k => v if !contains([
      "compute_max_instance_size",
      "compute_min_instance_size",
      "compute_scale_down_enabled"
    ], k)
  }

  effective_auto_scaling_analytics = var.auto_scaling_analytics == null ? (local.manual_compute_analytics ? {
    compute_enabled = false # Avoids the ANALYTICS_AUTO_SCALING_AMBIGUOUS error when auto_scaling is used for electable and manual instance size used for analytics
    } : null) : (
    local.auto_scaling_compute_enabled_analytics ? var.auto_scaling_analytics : {
      for k, v in var.auto_scaling_analytics :
      k => v if !contains([
        "compute_max_instance_size",
        "compute_min_instance_size",
        "compute_scale_down_enabled"
      ], k)
    }
  )

  # one replication_spec created per group in local.grouped_regions
  replication_specs_built = tolist([
    for gi in range(length(local.grouped_regions)) : {
      zone_name = local.is_geosharded ? split("||", local.geoshard_keys[gi])[0] : null


      region_configs = tolist([
        for region_index, r in local.grouped_regions[gi] : {
          provider_name          = r.provider_name != null ? r.provider_name : var.provider_name
          region_name            = r.name
          priority               = max(7 - region_index, 0)
          auto_scaling           = local.effective_auto_scaling
          analytics_auto_scaling = local.effective_auto_scaling_analytics

          electable_specs = r.node_count != null ? {
            # since disk_iops, disk_size_gb, ebs_volume_type are computed attributes setting them as null will not create a plan change even when API returns a different value
            # they are also not required by the API
            disk_iops       = try(coalesce(r.disk_iops, var.disk_iops), null)
            disk_size_gb    = try(coalesce(r.disk_size_gb, var.disk_size_gb), null)
            ebs_volume_type = try(coalesce(r.ebs_volume_type, var.ebs_volume_type), null)
            # instance_size is required by the API until effctive fields are supported
            instance_size = local.auto_scaling_compute_enabled ? try(
              local.existing_cluster.old_cluster.replication_specs[gi].region_configs[region_index].electable_specs.instance_size,
              local.effective_auto_scaling.compute_min_instance_size
            ) : coalesce(r.instance_size, var.instance_size, local.DEFAULT_INSTANCE_SIZE)
            node_count = r.node_count
          } : null

          read_only_specs = r.node_count_read_only != null ? {
            disk_iops       = try(coalesce(r.disk_iops, var.disk_iops), null)
            disk_size_gb    = try(coalesce(r.disk_size_gb, var.disk_size_gb), null)
            ebs_volume_type = try(coalesce(r.ebs_volume_type, var.ebs_volume_type), null)
            instance_size = local.auto_scaling_compute_enabled ? try(
              local.existing_cluster.old_cluster.replication_specs[gi].region_configs[region_index].read_only_specs.instance_size,
              local.effective_auto_scaling.compute_min_instance_size
            ) : coalesce(r.instance_size, var.instance_size, local.DEFAULT_INSTANCE_SIZE)
            node_count = r.node_count_read_only
          } : null

          analytics_specs = r.node_count_analytics != null ? {
            disk_iops       = try(coalesce(r.disk_iops, var.disk_iops), null)
            disk_size_gb    = try(coalesce(r.disk_size_gb, var.disk_size_gb), null)
            ebs_volume_type = try(coalesce(r.ebs_volume_type, var.ebs_volume_type), null)
            instance_size = local.effective_auto_scaling_analytics != null && local.effective_auto_scaling_analytics.compute_enabled ? try(
              local.existing_cluster.old_cluster.replication_specs[gi].region_configs[region_index].analytics_specs.instance_size,
              local.effective_auto_scaling_analytics.compute_min_instance_size
            ) : coalesce(r.instance_size_analytics, var.instance_size_analytics, local.DEFAULT_INSTANCE_SIZE)
            node_count = r.node_count_analytics
          } : null
        }
      ])
    }
  ])

  replication_specs_json = local.replication_specs_resource_var_used ? jsonencode(var.replication_specs) : jsonencode(local.replication_specs_built) # avoids "Mismatched list element types"
  empty_region_configs   = local.replication_specs_resource_var_used ? [] : [for idx, r in local.replication_specs_built : "replication_specs[${idx}].region_configs is empty" if length(r.region_configs) == 0]
  empty_regions          = length(local.regions) == 0

  // Validation messages (non-empty strings represent errors)
  validation_errors = compact(concat(
    local.empty_region_configs,

    // Mutual exclusivity
    length(var.regions) > 0 && local.replication_specs_resource_var_used ? ["Cannot use var.regions and var.replication_specs together, set regions=[] to use var.replication_specs"] : [],

    // Autoscaling vs fixed sizes
    var.auto_scaling.compute_enabled && var.instance_size != null ? ["Cannot set var.instance_size when auto_scaling is enabled. Set auto_scaling.compute_enabled=false to use fixed instance sizes"] : [],
    var.auto_scaling_analytics != null && var.instance_size_analytics != null ? ["Cannot use var.auto_scaling_analytics and var.instance_size_analytics together"] : [],

    // Autoscaling vs fixed sizes disk_gb
    local.auto_scaling_disk_enabled ?
    var.disk_size_gb != null ? ["Cannot set var.disk_size_gb when auto_scaling_disk is enabled. Set auto_scaling_disk=false to use fixed disk sizes"] : []
    : [],
    local.auto_scaling_disk_enabled ?
    [for idx, r in local.regions : r.disk_size_gb != null ? "Cannot use regions[*].disk_size_gb when auto_scaling_disk is enabled: index ${idx} disk_size_gb=${r.disk_size_gb}" : ""] : [],

    // Missing compute specification
    !local.manual_compute && !local.auto_scaling_compute_enabled && !local.auto_scaling_compute_enabled_analytics ? ["Must use auto-scaling or set instance_sizes"] : [],

    // Root level without manual_compute
    !local.manual_compute && var.disk_iops != null ? ["Cannot use disk_iops without setting instance_size (auto-scaling must be disabled)"] : [],
    !local.manual_compute && var.ebs_volume_type != null ? ["Cannot use ebs_volume_type without setting instance_size (auto-scaling must be disabled)"] : [],

    // Requires regions set
    var.instance_size != null && local.empty_regions && !local.replication_specs_resource_var_used ? ["Cannot use var.instance_size without var.regions"] : [],
    var.auto_scaling != null && local.empty_regions && !local.replication_specs_resource_var_used ? ["Cannot use var.auto_scaling without var.regions"] : [],
    var.auto_scaling_analytics != null && local.empty_regions && !local.replication_specs_resource_var_used ? ["Cannot use var.auto_scaling_analytics without var.regions"] : [],
    var.disk_iops != null && local.empty_regions && !local.replication_specs_resource_var_used ? ["Cannot use var.disk_iops without var.regions"] : [],
    var.ebs_volume_type != null && local.empty_regions && !local.replication_specs_resource_var_used ? ["Cannot use var.ebs_volume_type without var.regions"] : [],

    // Per-region invalid manual scaling parameters when autoscaling is used
    local.auto_scaling_compute_enabled ? [for idx, r in local.regions : r.instance_size != null ? "Cannot use regions[*].instance_size when auto_scaling is enabled: index ${idx} instance_size=${r.instance_size}" : ""] : [],
    local.auto_scaling_compute_enabled ? [for idx, r in local.regions : r.disk_iops != null ? "Cannot use regions[*].disk_iops when auto_scaling is enabled: index ${idx} disk_iops=${r.disk_iops}" : ""] : [],
    local.auto_scaling_compute_enabled ? [for idx, r in local.regions : r.ebs_volume_type != null ? "Cannot use regions[*].ebs_volume_type when auto_scaling is enabled: index ${idx} ebs_volume_type=${r.ebs_volume_type}" : ""] : [],

    local.auto_scaling_compute_enabled_analytics ? [for idx, r in local.regions : r.instance_size_analytics != null ? "Cannot use regions[*].instance_size_analytics when auto_scaling_analytics is used: index ${idx} instance_size_analytics=${r.instance_size_analytics}" : ""] : [],

    // Cluster type vs region fields
    local.is_geosharded ? concat(
      [for idx, r in local.regions : (r.zone_name == null || trimspace(r.zone_name) == "") ? "Must use regions[*].zone_name when cluster_type is GEOSHARDED: zone_name missing @ index ${idx}" : ""],
      length(local.invalid_geo_zones_mixed) > 0 ? ["GEOSHARDED validation: Each zone must either set shard_number on all regions or on none. Mixed usage in zones: ${join(", ", local.invalid_geo_zones_mixed)}"] : []
    ) : [],

    local.sharded_validation_errors,

    local.is_replicaset ? concat(
      [for idx, r in local.regions : r.shard_number != null ? "Replicaset cluster should not define shard_number: regions[${idx}].shard_number=${r.shard_number}" : ""],
      [for idx, r in local.regions : r.zone_name != null ? "Replicaset cluster should not define zone_name: regions[${idx}].zone_name=${r.zone_name}" : ""]
    ) : [],

    local.is_geosharded && length(local.invalid_geo_zones_mixed) > 0 ? [
      "GEOSHARDED validation: Each zone must either set shard_number on all regions or on none. Mixed usage in zones: ${join(", ", local.invalid_geo_zones_mixed)}"
    ] : [],

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

  cluster_type                                     = var.cluster_type
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
