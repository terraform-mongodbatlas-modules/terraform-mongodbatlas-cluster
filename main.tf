locals {
  DEFAULT_INSTANCE_SIZE = "M10"

  # pit_enabled: null → inherit from backup_enabled, explicit value → use as-is
  effective_pit_enabled = coalesce(var.pit_enabled, var.backup_enabled)

  feature_set_tls = var.default_feature_set == "RECOMMENDED" ? "TLS1_3" : null

  effective_advanced_configuration = var.advanced_configuration == null ? null : merge(
    var.advanced_configuration,
    {
      minimum_enabled_tls_protocol = (
        var.advanced_configuration.minimum_enabled_tls_protocol != null
        ? var.advanced_configuration.minimum_enabled_tls_protocol
        : local.feature_set_tls
      )
    }
  )

  regions = coalesce(var.regions, [])

  is_geosharded                       = var.cluster_type == "GEOSHARDED"
  is_sharded                          = var.cluster_type == "SHARDED"
  is_replicaset                       = var.cluster_type == "REPLICASET"
  replication_specs_resource_var_used = length(var.replication_specs) > 0

  # ---- REPLICASET  ----
  grouped_regions_replicaset = local.is_replicaset ? [local.regions] : []

  # ---- SHARDED  ----
  sharded_uniform       = local.is_sharded && var.shard_count != null
  sharded_explicit      = local.is_sharded && var.shard_count == null
  has_any_zone_in_shard = local.is_sharded && anytrue([for r in local.regions : r.zone_name != null && try(trimspace(r.zone_name), "") != ""])
  has_any_name_in_shard = local.is_sharded && anytrue([for r in local.regions : r.shard_name != null])
  all_have_identity_in_shard = local.is_sharded && length(local.regions) > 0 && alltrue([
    for r in local.regions : r.shard_name != null
  ])
  sharded_validation_errors = local.is_sharded && !local.replication_specs_resource_var_used ? compact(concat(
    local.has_any_zone_in_shard
    ? ["SHARDED validation: do not set regions[*].zone_name."] : [],

    (local.sharded_uniform && local.has_any_name_in_shard)
    ? ["SHARDED validation: when shard_count is set, do not set regions[*].shard_name."] : [],

    (!local.sharded_uniform && !local.all_have_identity_in_shard)
    ? ["SHARDED validation: set regions[*].shard_name on every region (or use shard_count)."] : [],

    (local.sharded_uniform && length(local.regions) == 0)
    ? ["SHARDED: when shard_count is set, you must define at least one region."] : []
  )) : []

  # shard_name groups follow first appearance in regions.
  unique_shard_names = local.sharded_explicit ? distinct([
    for r in local.regions : r.shard_name if r.shard_name != null
  ]) : []

  grouped_regions_sharded_explicit = local.sharded_explicit ? [
    for sn in local.unique_shard_names :
    [for r in local.regions : r if r.shard_name == sn]
  ] : []

  grouped_regions_sharded_uniform = local.sharded_uniform ? [
    for _i in range(var.shard_count) : local.regions
  ] : []

  # ---- GEOSHARDED  ----
  geo_rows = local.is_geosharded ? [
    for r in local.regions : r
    if r.zone_name != null && try(trimspace(r.zone_name), "") != ""
  ] : []

  unique_zone_names = local.is_geosharded ? distinct([
    for r in local.geo_rows : trimspace(r.zone_name)
  ]) : []

  # Per zone: all-or-none shard_name identity.
  zones_with_counts = local.is_geosharded ? {
    for z in local.unique_zone_names :
    z => {
      with_id    = length([for r in local.geo_rows : r if trimspace(r.zone_name) == z && r.shard_name != null])
      without_id = length([for r in local.geo_rows : r if trimspace(r.zone_name) == z && r.shard_name == null])
    }
  } : {}

  invalid_geo_zones_mixed = local.is_geosharded ? [
    for z, c in local.zones_with_counts :
    z if(c.with_id > 0 && c.without_id > 0)
  ] : []

  # True when every region in the zone sets an explicit shard_name;
  # false means the zone is a single default shard.
  zone_has_shard_identity = local.is_geosharded ? {
    for z, c in local.zones_with_counts : z => (c.with_id > 0 && c.without_id == 0)
  } : {}

  shard_names_in_multiple_zones = local.is_geosharded ? [
    for name in distinct([for r in local.geo_rows : r.shard_name if r.shard_name != null]) :
    name if length(distinct([for r in local.geo_rows : trimspace(r.zone_name) if r.shard_name == name])) > 1
  ] : []

  # Keys: named shard = shard_name; single-shard zone = zone||single.
  geo_keyed_rows = local.is_geosharded ? [
    for r in local.geo_rows : {
      key    = !local.zone_has_shard_identity[trimspace(r.zone_name)] ? "${trimspace(r.zone_name)}||single" : r.shard_name
      region = r
    }
  ] : []

  # Global first-appearance order across all zones, so interleaved
  # zones keep their original replication_specs sequence and stay no-op on upgrade.
  geoshard_keys = local.is_geosharded ? distinct([
    for x in local.geo_keyed_rows : x.key
  ]) : []

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

  # ---- Backup schedule ----
  create_backup_schedule = var.backup_enabled && var.backup_mode != "UNMANAGED"

  # Topology candidates for backup_copy_region auto-derivation (first shard/zone group).
  backup_copy_candidate_regions = length(local.grouped_regions) > 0 ? local.grouped_regions[0] : []

  # Ternaries, not && -- see tests/plan_short_circuit.tftest.hcl.
  # region_count defaults to 1 when omitted; an explicit value is validated for range below.
  backup_copy_region_count = var.backup_copy_region == null ? 0 : coalesce(try(var.backup_copy_region.region_count, null), 1)
  # The count-based branch only slices when the count is in range, so an out-of-range count is reported by
  # local.backup_copy_region_validation_errors instead of raising a raw slice error.
  backup_copy_derived_targets = local.backup_copy_region_count <= length(local.backup_copy_candidate_regions) - 1 ? [
    for r in slice(local.backup_copy_candidate_regions, 1, 1 + local.backup_copy_region_count) : {
      name          = r.name
      provider_name = r.provider_name
    }
  ] : []

  # One copy target per requested secondary region. `region` pins one, `regions` names a subset explicitly,
  # otherwise `region_count` takes the highest-priority secondaries from the cluster's first region group.
  # List comprehensions, not a keyed map: a multi-cloud region group can repeat a region name across
  # providers (AWS and AZURE both have US_EAST_2), which a `{for ... : r.name => ...}` map rejects.
  backup_copy_targets = var.backup_copy_region == null ? [] : (
    var.backup_copy_region.region != null ? [{
      name          = var.backup_copy_region.region
      provider_name = try([for r in local.backup_copy_candidate_regions : r.provider_name if r.name == var.backup_copy_region.region][0], null)
      }] : (
      var.backup_copy_region.regions != null ? [
        for name in var.backup_copy_region.regions : {
          name          = name
          provider_name = try([for r in local.backup_copy_candidate_regions : r.provider_name if r.name == name][0], null)
        }
      ] : local.backup_copy_derived_targets
    )
  )

  # Disambiguates which zone the copy target belongs to -- required by the underlying Atlas API even
  # though the provider marks it optional/computed. Index 0 always matches the same first shard/zone
  # group backup_copy_candidate_regions derives region_name/cloud_provider from (see comment above).
  backup_copy_zone_id = var.backup_copy_region == null ? null : try(mongodbatlas_advanced_cluster.this.replication_specs[0].zone_id, null)

  # One copy_settings entry per target. `cloud_provider` stays null (left for the provider to infer) only
  # when neither the override, the target region, nor the root provider_name can resolve it.
  backup_copy_settings = var.backup_copy_region == null ? [] : [
    for t in local.backup_copy_targets : {
      cloud_provider = var.backup_copy_region.cloud_provider != null ? var.backup_copy_region.cloud_provider : (
        t.provider_name != null ? t.provider_name : var.provider_name
      )
      region_name              = t.name
      zone_id                  = local.backup_copy_zone_id
      should_copy_oplogs       = coalesce(var.backup_copy_region.should_copy_oplogs, local.effective_pit_enabled)
      last_number_of_snapshots = var.backup_copy_region.last_number_of_snapshots
    }
  ]

  # Request-level (not per target) copy-snapshot lifecycle flags.
  backup_copy_update_snapshots = var.backup_copy_region == null ? null : try(var.backup_copy_region.update_copy_snapshots, null)
  backup_copy_delete_snapshots = var.backup_copy_region == null ? null : try(var.backup_copy_region.delete_copy_snapshots, null)

  # Ternaries, not && -- see tests/plan_short_circuit.tftest.hcl.
  backup_copy_derives_by_count = var.backup_copy_region == null ? false : (
    var.backup_copy_region.region == null && var.backup_copy_region.regions == null
  )

  backup_copy_region_validation_errors = var.backup_copy_region == null ? [] : compact(concat(
    # region_count = 0 derives no targets, so it does not need a second region.
    # region_count = 0 derives no targets, so it does not need a second region and cannot exceed any.
    local.backup_copy_derives_by_count && local.backup_copy_region_count > 0 && length(local.backup_copy_candidate_regions) < 2 ? [
      "backup_copy_region = {} needs at least 2 regions in `regions` to derive a copy target from. Add a region or set backup_copy_region.region."
    ] : [],

    local.backup_copy_derives_by_count && local.backup_copy_region_count > 0 && local.backup_copy_region_count > length(local.backup_copy_candidate_regions) - 1 ? [
      "backup_copy_region.region_count = ${local.backup_copy_region_count} is greater than the ${max(length(local.backup_copy_candidate_regions) - 1, 0)} secondary region(s) in `regions`. Add a region or lower region_count."
    ] : [],

    # An explicit list must name secondary regions, with no duplicates (Atlas rejects a duplicate copy destination).
    var.backup_copy_region.regions != null ? compact(concat(
      [for name in var.backup_copy_region.regions :
        length([for r in local.backup_copy_candidate_regions : r if r.name == name]) == 0 || name == try(local.backup_copy_candidate_regions[0].name, null)
        ? "backup_copy_region.regions: '${name}' must be a secondary region in `regions` (not the primary)." : ""
      ],
      length(distinct(var.backup_copy_region.regions)) != length(var.backup_copy_region.regions)
      ? ["backup_copy_region.regions: duplicate copy targets are not allowed."] : [],
    )) : [],
  ))

  # auto scaling for electable nodes
  auto_scaling_compute_enabled = var.auto_scaling.compute_enabled
  auto_scaling_disk_enabled    = var.auto_scaling.disk_gb_enabled
  manual_compute_electable     = var.instance_size != null || length([for idx, r in local.regions : idx if r.instance_size != null]) > 0

  excluded_auto_scaling_fields = concat(
    local.auto_scaling_compute_enabled ? [] : ["compute_max_instance_size", "compute_min_instance_size", "compute_scale_down_enabled"],
    local.auto_scaling_compute_enabled && var.auto_scaling.compute_scale_down_enabled ? [] : ["compute_min_instance_size"],
  )
  effective_auto_scaling = { for k, v in var.auto_scaling : k => v if !contains(local.excluded_auto_scaling_fields, k) }
  # auto scaling for analytics nodes
  manual_compute_analytics         = var.instance_size_analytics != null || length([for idx, r in local.regions : idx if r.instance_size_analytics != null]) > 0
  analytics_auto_scaling_undefined = var.auto_scaling_analytics == null && !local.manual_compute_analytics
  auto_scaling_compute_enabled_analytics = coalesce(
    local.manual_compute_analytics ? false : null,
    try(var.auto_scaling_analytics.compute_enabled, null),
    local.analytics_auto_scaling_undefined ? local.auto_scaling_compute_enabled : null,
  )
  excluded_auto_scaling_analytics_fields = concat(
    local.auto_scaling_compute_enabled_analytics ? [] : ["compute_max_instance_size", "compute_min_instance_size", "compute_scale_down_enabled"],
    # When compute_scale_down_enabled is not specified in auto_scaling_analytics, default to true
    # (consistent with electable nodes default behavior)
    local.auto_scaling_compute_enabled_analytics && try(var.auto_scaling_analytics.compute_scale_down_enabled, true) ? [] : ["compute_min_instance_size"],
  )
  analytics_auto_scaling_options = {
    # When auto_scaling_analytics is null and no manual instance_size_analytics is set,
    # inherit the electable auto_scaling configuration for analytics nodes
    undefined = local.effective_auto_scaling
    manual = {
      compute_enabled = false # Avoids the ANALYTICS_AUTO_SCALING_AMBIGUOUS error when auto_scaling is used for electable and manual instance size used for analytics
    }
    user_defined = var.auto_scaling_analytics != null ? { for k, v in var.auto_scaling_analytics : k => v if !contains(local.excluded_auto_scaling_analytics_fields, k) } : null
  }
  analytics_auto_scaling_active_option = local.analytics_auto_scaling_undefined ? "undefined" : local.manual_compute_analytics ? "manual" : "user_defined"
  effective_auto_scaling_analytics     = local.analytics_auto_scaling_options[local.analytics_auto_scaling_active_option]

  # manual compute for electable or analytics nodes
  manual_compute = local.manual_compute_electable || local.manual_compute_analytics

  # Resolved analytics auto-scaling bounds (inherit electable when analytics config omits a field).
  analytics_compute_max_instance_size = coalesce(
    try(var.auto_scaling_analytics.compute_max_instance_size, null),
    var.auto_scaling.compute_max_instance_size,
  )
  analytics_compute_min_instance_size = coalesce(
    try(var.auto_scaling_analytics.compute_min_instance_size, null),
    var.auto_scaling.compute_min_instance_size,
    local.DEFAULT_INSTANCE_SIZE,
  )
  # Inherit electable when auto_scaling_analytics is omitted (undefined); when explicitly set,
  # an omitted compute_scale_down_enabled defaults to true (matches effective_auto_scaling_analytics
  # and the auto_scaling_analytics variable contract).
  analytics_compute_scale_down_enabled = local.analytics_auto_scaling_undefined ? var.auto_scaling.compute_scale_down_enabled : try(var.auto_scaling_analytics.compute_scale_down_enabled, true)

  # Auto-scaling instance_size inputs for electable / read-only / analytics (modules/_autoscaling_instance_size).
  autoscaling_instance_size_requests = merge(
    {
      for item in flatten([
        for gi, group in local.grouped_regions : [
          for region_index, r in group : {
            key = "electable.${gi}.${region_index}"
            existing = try(
              local.existing_cluster.old_cluster.replication_specs[gi].region_configs[region_index].electable_specs.instance_size,
              null,
            )
          } if local.auto_scaling_compute_enabled && r.node_count != null
        ]
        ]) : item.key => {
        existing                   = item.existing
        compute_max_instance_size  = var.auto_scaling.compute_max_instance_size
        compute_min_instance_size  = var.auto_scaling.compute_min_instance_size
        compute_scale_down_enabled = var.auto_scaling.compute_scale_down_enabled
      }
    },
    {
      for item in flatten([
        for gi, group in local.grouped_regions : [
          for region_index, r in group : {
            key = "read_only.${gi}.${region_index}"
            existing = try(
              local.existing_cluster.old_cluster.replication_specs[gi].region_configs[region_index].read_only_specs.instance_size,
              null,
            )
          } if local.auto_scaling_compute_enabled && r.node_count_read_only != null
        ]
        ]) : item.key => {
        existing                   = item.existing
        compute_max_instance_size  = var.auto_scaling.compute_max_instance_size
        compute_min_instance_size  = var.auto_scaling.compute_min_instance_size
        compute_scale_down_enabled = var.auto_scaling.compute_scale_down_enabled
      }
    },
    {
      for item in flatten([
        for gi, group in local.grouped_regions : [
          for region_index, r in group : {
            key = "analytics.${gi}.${region_index}"
            existing = try(
              local.existing_cluster.old_cluster.replication_specs[gi].region_configs[region_index].analytics_specs.instance_size,
              null,
            )
          } if local.auto_scaling_compute_enabled_analytics && r.node_count_analytics != null
        ]
        ]) : item.key => {
        existing                   = item.existing
        compute_max_instance_size  = local.analytics_compute_max_instance_size
        compute_min_instance_size  = local.analytics_compute_min_instance_size
        compute_scale_down_enabled = local.analytics_compute_scale_down_enabled
      }
    },
  )
}

module "autoscaling_instance_size" {
  source   = "./modules/_autoscaling_instance_size"
  for_each = local.autoscaling_instance_size_requests

  existing_instance_size     = each.value.existing
  compute_max_instance_size  = each.value.compute_max_instance_size
  compute_min_instance_size  = each.value.compute_min_instance_size
  compute_scale_down_enabled = each.value.compute_scale_down_enabled
}

locals {
  # Electable regions get 7, 6, 5... in list order. Atlas requires priority 0 when a
  # region has only analyticsSpecs / readOnlySpecs (no electableSpecs).
  region_priorities = [
    for group in local.grouped_regions : [
      for region_index, r in group :
      r.node_count != null ? max(7 - length([
        for i, x in group : i if i < region_index && x.node_count != null
      ]), 0) : 0
    ]
  ]

  # Atlas requires descending priorities. Non-electable regions get 0, so they must
  # follow electable regions within each replica set, shard, or zone.
  non_electable_before_electable_errors = [
    for gi, group in local.grouped_regions :
    alltrue([
      for i, r in group :
      r.node_count != null ? true : length([
        for j, x in group : j if j > i ? x.node_count != null : false
      ]) == 0
    ]) ? "" : "List electable regions (node_count) first within each replica set, shard, or zone. replication_specs[${gi}] lists an analytics-only or read-only-only region before an electable region."
  ]

  # one replication_spec created per group in local.grouped_regions
  replication_specs_built = tolist([
    for gi in range(length(local.grouped_regions)) : {
      zone_name = local.is_geosharded ? trimspace(local.grouped_regions[gi][0].zone_name) : null


      region_configs = tolist([
        for region_index, r in local.grouped_regions[gi] : {
          provider_name          = r.provider_name != null ? r.provider_name : var.provider_name
          region_name            = r.name
          priority               = local.region_priorities[gi][region_index]
          auto_scaling           = local.effective_auto_scaling
          analytics_auto_scaling = local.effective_auto_scaling_analytics

          electable_specs = r.node_count != null ? {
            # since disk_iops, disk_size_gb, ebs_volume_type are computed attributes setting them as null will not create a plan change even when API returns a different value
            # they are also not required by the API
            disk_iops       = try(coalesce(r.disk_iops, var.disk_iops), null)
            disk_size_gb    = try(coalesce(r.disk_size_gb, var.disk_size_gb), null)
            ebs_volume_type = try(coalesce(r.ebs_volume_type, var.ebs_volume_type), null)
            # instance_size is required by the API until effective fields are supported
            instance_size = local.auto_scaling_compute_enabled ? module.autoscaling_instance_size["electable.${gi}.${region_index}"].instance_size : coalesce(r.instance_size, var.instance_size, local.DEFAULT_INSTANCE_SIZE)
            node_count    = r.node_count
          } : null

          read_only_specs = r.node_count_read_only != null ? {
            disk_iops       = try(coalesce(r.disk_iops, var.disk_iops), null)
            disk_size_gb    = try(coalesce(r.disk_size_gb, var.disk_size_gb), null)
            ebs_volume_type = try(coalesce(r.ebs_volume_type, var.ebs_volume_type), null)
            instance_size   = local.auto_scaling_compute_enabled ? module.autoscaling_instance_size["read_only.${gi}.${region_index}"].instance_size : coalesce(r.instance_size, var.instance_size, local.DEFAULT_INSTANCE_SIZE)
            node_count      = r.node_count_read_only
          } : null

          analytics_specs = r.node_count_analytics != null ? {
            disk_iops       = try(coalesce(r.disk_iops, var.disk_iops), null)
            disk_size_gb    = try(coalesce(r.disk_size_gb, var.disk_size_gb), null)
            ebs_volume_type = try(coalesce(r.ebs_volume_type, var.ebs_volume_type), null)
            instance_size   = local.auto_scaling_compute_enabled_analytics ? module.autoscaling_instance_size["analytics.${gi}.${region_index}"].instance_size : coalesce(r.instance_size_analytics, var.instance_size_analytics, local.DEFAULT_INSTANCE_SIZE)
            node_count      = r.node_count_analytics
          } : null
        }
      ])
    }
  ])

  replication_specs_json = local.replication_specs_resource_var_used ? jsonencode(var.replication_specs) : jsonencode(local.replication_specs_built) # avoids "Mismatched list element types"
  empty_regions          = length(local.regions) == 0
  # Validation messages (non-empty strings represent errors)
  validation_errors_regions_usage = local.replication_specs_resource_var_used ? [] : compact(concat(
    # Regions variable usage validations
    [for idx, r in local.replication_specs_built : "replication_specs[${idx}].region_configs is empty" if length(r.region_configs) == 0],
    local.non_electable_before_electable_errors,
    # Autoscaling vs fixed sizes
    var.auto_scaling.compute_enabled && var.instance_size != null ? ["Cannot set var.instance_size when auto_scaling is enabled. Set auto_scaling.compute_enabled=false to use fixed instance sizes"] : [],
    var.auto_scaling_analytics != null && var.instance_size_analytics != null ? ["Cannot use var.auto_scaling_analytics and var.instance_size_analytics together"] : [],

    # Autoscaling vs fixed sizes disk_gb
    local.auto_scaling_disk_enabled ?
    var.disk_size_gb != null ? ["Cannot set var.disk_size_gb when auto_scaling_disk is enabled. Set auto_scaling_disk=false to use fixed disk sizes"] : []
    : [],
    local.auto_scaling_disk_enabled ?
    [for idx, r in local.regions : r.disk_size_gb != null ? "Cannot use regions[*].disk_size_gb when auto_scaling_disk is enabled: index ${idx} disk_size_gb=${r.disk_size_gb}" : ""] : [],

    # Missing compute specification
    !local.manual_compute && !local.auto_scaling_compute_enabled && !local.auto_scaling_compute_enabled_analytics ? ["Must use auto-scaling or set instance_sizes"] : [],

    # Root level without manual_compute
    !local.manual_compute && var.disk_iops != null ? ["Cannot use disk_iops without setting instance_size (auto-scaling must be disabled)"] : [],
    !local.manual_compute && var.ebs_volume_type != null ? ["Cannot use ebs_volume_type without setting instance_size (auto-scaling must be disabled)"] : [],
    # Requires regions set
    var.instance_size != null && local.empty_regions ? ["Cannot use var.instance_size without var.regions"] : [],
    var.auto_scaling != null && local.empty_regions ? ["Cannot use var.auto_scaling without var.regions"] : [],
    var.auto_scaling_analytics != null && local.empty_regions ? ["Cannot use var.auto_scaling_analytics without var.regions"] : [],
    var.disk_iops != null && local.empty_regions ? ["Cannot use var.disk_iops without var.regions"] : [],
    var.ebs_volume_type != null && local.empty_regions ? ["Cannot use var.ebs_volume_type without var.regions"] : [],

    # Per-region invalid manual scaling parameters when autoscaling is used
    local.auto_scaling_compute_enabled ? [for idx, r in local.regions : r.instance_size != null ? "Cannot use regions[*].instance_size when auto_scaling is enabled: index ${idx} instance_size=${r.instance_size}" : ""] : [],
    local.auto_scaling_compute_enabled ? [for idx, r in local.regions : r.disk_iops != null ? "Cannot use regions[*].disk_iops when auto_scaling is enabled: index ${idx} disk_iops=${r.disk_iops}" : ""] : [],
    local.auto_scaling_compute_enabled ? [for idx, r in local.regions : r.ebs_volume_type != null ? "Cannot use regions[*].ebs_volume_type when auto_scaling is enabled: index ${idx} ebs_volume_type=${r.ebs_volume_type}" : ""] : [],

    local.auto_scaling_compute_enabled_analytics ? [for idx, r in local.regions : r.instance_size_analytics != null ? "Cannot use regions[*].instance_size_analytics when auto_scaling_analytics is used: index ${idx} instance_size_analytics=${r.instance_size_analytics}" : ""] : [],
    # Cluster type vs region fields
    local.is_geosharded ? concat(
      [for idx, r in local.regions : (r.zone_name == null || try(trimspace(r.zone_name), "") == "") ? "Must use regions[*].zone_name when cluster_type is GEOSHARDED: zone_name missing @ index ${idx}" : ""],
      length(local.invalid_geo_zones_mixed) > 0 ? ["GEOSHARDED validation: Each zone must either set shard_name on all regions or on none. Mixed usage in zones: ${join(", ", local.invalid_geo_zones_mixed)}"] : [],
      length(local.shard_names_in_multiple_zones) > 0 ? ["GEOSHARDED validation: regions[*].shard_name must be unique across the cluster. Duplicates across zones: ${join(", ", local.shard_names_in_multiple_zones)}"] : []
    ) : [],
    local.is_replicaset ? concat(
      [for idx, r in local.regions : r.shard_name != null ? "Replicaset cluster should not define shard_name: regions[${idx}].shard_name=${r.shard_name}" : ""],
      [for idx, r in local.regions : r.zone_name != null ? "Replicaset cluster should not define zone_name: regions[${idx}].zone_name=${r.zone_name}" : ""]
    ) : [],
    # Provider name presence
    var.provider_name == null ? [for idx, r in local.regions : r.provider_name == null ? "Must use regions[*].provider_name when root provider_name is not specified: regions[${idx}].provider_name is missing" : ""] : [],
    local.sharded_validation_errors,
  ))

  validation_errors = compact(concat(
    # Mutual exclusivity: regions vs replication_specs
    length(local.regions) > 0 && local.replication_specs_resource_var_used ? ["Cannot use var.regions and var.replication_specs together, set regions=[] to use var.replication_specs"] : [],
    local.validation_errors_regions_usage,
    local.backup_copy_region_validation_errors,
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
  advanced_configuration                           = local.effective_advanced_configuration
  backup_enabled                                   = var.backup_enabled
  bi_connector_config                              = var.bi_connector_config
  config_server_management_mode                    = local.is_sharded || local.is_geosharded ? var.config_server_management_mode : null
  delete_on_create_timeout                         = var.delete_on_create_timeout
  encryption_at_rest_provider                      = var.encryption_at_rest_provider
  global_cluster_self_managed_sharding             = var.global_cluster_self_managed_sharding
  mongo_db_major_version                           = var.mongo_db_major_version
  paused                                           = var.paused
  pinned_fcv                                       = var.pinned_fcv
  pit_enabled                                      = local.effective_pit_enabled
  redact_client_log_data                           = var.redact_client_log_data
  replica_set_scaling_strategy                     = var.replica_set_scaling_strategy
  retain_backups_enabled                           = var.retain_backups_enabled
  root_cert_type                                   = var.root_cert_type
  tags                                             = var.tags
  termination_protection_enabled                   = var.termination_protection_enabled
  timeouts                                         = var.timeouts
  version_release_system                           = var.version_release_system
}

module "backup_schedule" {
  count  = local.create_backup_schedule ? 1 : 0
  source = "./modules/cloud_backup_schedule"

  project_id   = var.project_id
  cluster_name = mongodbatlas_advanced_cluster.this.name
  backup_mode  = var.backup_mode

  retention = var.backup_retention != null ? var.backup_retention : {
    skip_default_retentions  = false
    restore_window_days      = null
    reference_hour_of_day    = null
    reference_minute_of_hour = null
    ondemand                 = null
    hourly                   = null
    daily                    = null
    weekly                   = null
    monthly                  = null
    yearly                   = null
  }
  copy_settings             = local.backup_copy_settings
  copy_policy_items_enabled = var.backup_copy_region != null
  update_copy_snapshots     = local.backup_copy_update_snapshots
  delete_copy_snapshots     = local.backup_copy_delete_snapshots
  export                    = var.backup_export
  skip_destroy              = var.backup_schedule_skip_destroy
}
