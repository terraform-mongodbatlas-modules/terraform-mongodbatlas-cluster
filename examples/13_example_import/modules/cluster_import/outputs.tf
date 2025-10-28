# Core module variables
output "name" {
  description = "Cluster name"
  value       = local.cluster.name
}

output "regions" {
  description = "Transformed regions configuration for the cluster module"
  value       = local.regions_transformed
}

output "provider_name" {
  description = "Common provider name across all regions (if all regions use the same provider)"
  value       = local.common_provider_name
}

output "instance_size" {
  description = "Instance size for electable/read-only nodes (when not using auto-scaling)"
  value       = local.common_instance_size
}

output "disk_size_gb" {
  description = "Disk size in GB"
  value       = local.common_disk_size_gb
}

output "disk_iops" {
  description = "Disk IOPS"
  value       = local.common_disk_iops
}

output "ebs_volume_type" {
  description = "EBS volume type (for AWS)"
  value       = local.common_ebs_volume_type
}

output "instance_size_analytics" {
  description = "Instance size for analytics nodes (when not using auto-scaling)"
  value       = local.common_instance_size_analytics
}

output "auto_scaling" {
  description = "Auto scaling configuration for electable/read-only nodes (null if matches module defaults)"
  value       = local.auto_scaling
}

output "auto_scaling_analytics" {
  description = "Auto scaling configuration for analytics nodes"
  value = local.analytics_auto_scaling != null ? {
    compute_enabled            = local.analytics_auto_scaling.compute_enabled
    compute_max_instance_size  = local.analytics_auto_scaling.compute_max_instance_size != "" ? local.analytics_auto_scaling.compute_max_instance_size : null
    compute_min_instance_size  = local.analytics_auto_scaling.compute_min_instance_size != "" ? local.analytics_auto_scaling.compute_min_instance_size : null
    compute_scale_down_enabled = local.analytics_auto_scaling.compute_scale_down_enabled
    disk_gb_enabled            = local.analytics_auto_scaling.disk_gb_enabled
  } : null
}

output "tags" {
  description = "Resource tags (null if empty)"
  value       = length(local.cluster.tags) > 0 ? local.cluster.tags : null
}

output "shard_count" {
  description = "Number of shards (only for SHARDED clusters with identical shard topology)"
  value       = local.use_shard_count ? local.shard_count : null
}

# Additional cluster properties that might be useful

output "cluster_type" {
  description = "Cluster type (REPLICASET, SHARDED, or GEOSHARDED)"
  value       = local.cluster.cluster_type
}

output "mongo_db_major_version" {
  description = "MongoDB major version (null if empty)"
  value       = local.cluster.mongo_db_major_version != "" ? local.cluster.mongo_db_major_version : null
}

output "backup_enabled" {
  description = "Whether backup is enabled (null if matches default of true)"
  value       = local.cluster.backup_enabled != true ? local.cluster.backup_enabled : null
}

output "pit_enabled" {
  description = "Whether point-in-time restore is enabled (null if matches default of true)"
  value       = local.cluster.pit_enabled != true ? local.cluster.pit_enabled : null
}

output "termination_protection_enabled" {
  description = "Whether termination protection is enabled (null if not set)"
  value       = local.cluster.termination_protection_enabled
}

output "redact_client_log_data" {
  description = "Whether to redact client log data (null if matches default of true)"
  value       = local.cluster.redact_client_log_data != true ? local.cluster.redact_client_log_data : null
}

output "encryption_at_rest_provider" {
  description = "Encryption at rest provider (null if NONE or empty)"
  value       = local.cluster.encryption_at_rest_provider != "NONE" && local.cluster.encryption_at_rest_provider != "" ? local.cluster.encryption_at_rest_provider : null
}

output "version_release_system" {
  description = "Version release system (LTS or CONTINUOUS, null if empty or default LTS)"
  value       = local.cluster.version_release_system != "" && local.cluster.version_release_system != "LTS" ? local.cluster.version_release_system : null
}

output "replica_set_scaling_strategy" {
  description = "Replica set scaling strategy (null if not set)"
  value       = local.cluster.replica_set_scaling_strategy != "" ? local.cluster.replica_set_scaling_strategy : null
}

output "advanced_configuration" {
  description = "Advanced configuration settings (null if all values match defaults)"
  value       = local.advanced_configuration_has_values ? local.advanced_configuration_filtered : null
}

output "bi_connector_config" {
  description = "BI Connector configuration (null if disabled)"
  value = local.cluster.bi_connector_config.enabled ? {
    enabled         = local.cluster.bi_connector_config.enabled
    read_preference = local.cluster.bi_connector_config.read_preference
  } : null
}

output "global_cluster_self_managed_sharding" {
  description = "Global cluster self-managed sharding (null if false or not applicable)"
  value       = local.cluster.global_cluster_self_managed_sharding ? local.cluster.global_cluster_self_managed_sharding : null
}

# Summary output for easy review
output "summary" {
  description = "Human-readable summary of the cluster configuration"
  value = {
    cluster_name         = local.cluster.name
    cluster_type         = local.cluster.cluster_type
    mongodb_version      = local.cluster.mongo_db_major_version
    number_of_shards     = length(local.cluster.replication_specs)
    number_of_regions    = length(local.all_regions_with_shard_info)
    region_names         = distinct([for r in local.all_regions_with_shard_info : r.name])
    providers            = distinct([for r in local.all_regions_with_shard_info : r.provider_name])
    instance_sizes       = distinct([for r in local.all_regions_with_shard_info : r.instance_size if r.instance_size != ""])
    auto_scaling_enabled = local.auto_scaling_raw.compute_enabled
  }
}
