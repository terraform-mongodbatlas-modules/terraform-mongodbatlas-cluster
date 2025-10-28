# Core module variables (delegated to submodule)
output "name" {
  description = "Cluster name"
  value       = module.cluster_import.name
}

output "regions" {
  description = "Transformed regions configuration for the cluster module"
  value       = module.cluster_import.regions
}

output "provider_name" {
  description = "Common provider name across all regions (if all regions use the same provider)"
  value       = module.cluster_import.provider_name
}

output "instance_size" {
  description = "Instance size for electable/read-only nodes (when not using auto-scaling)"
  value       = module.cluster_import.instance_size
}

output "disk_size_gb" {
  description = "Disk size in GB"
  value       = module.cluster_import.disk_size_gb
}

output "disk_iops" {
  description = "Disk IOPS"
  value       = module.cluster_import.disk_iops
}

output "ebs_volume_type" {
  description = "EBS volume type (for AWS)"
  value       = module.cluster_import.ebs_volume_type
}

output "instance_size_analytics" {
  description = "Instance size for analytics nodes (when not using auto-scaling)"
  value       = module.cluster_import.instance_size_analytics
}

output "auto_scaling" {
  description = "Auto scaling configuration for electable/read-only nodes (null if matches defaults)"
  value       = module.cluster_import.auto_scaling
}

output "auto_scaling_analytics" {
  description = "Auto scaling configuration for analytics nodes"
  value       = module.cluster_import.auto_scaling_analytics
}

output "tags" {
  description = "Resource tags (null if empty)"
  value       = module.cluster_import.tags
}

output "shard_count" {
  description = "Number of shards (only for SHARDED clusters with identical shard topology)"
  value       = module.cluster_import.shard_count
}

# Additional cluster properties that might be useful

output "cluster_type" {
  description = "Cluster type (REPLICASET, SHARDED, or GEOSHARDED)"
  value       = module.cluster_import.cluster_type
}

output "mongo_db_major_version" {
  description = "MongoDB major version (null if empty)"
  value       = module.cluster_import.mongo_db_major_version
}

output "backup_enabled" {
  description = "Whether backup is enabled (null if matches default)"
  value       = module.cluster_import.backup_enabled
}

output "pit_enabled" {
  description = "Whether point-in-time restore is enabled (null if matches default)"
  value       = module.cluster_import.pit_enabled
}

output "termination_protection_enabled" {
  description = "Whether termination protection is enabled"
  value       = module.cluster_import.termination_protection_enabled
}

output "redact_client_log_data" {
  description = "Whether to redact client log data (null if matches default)"
  value       = module.cluster_import.redact_client_log_data
}

output "encryption_at_rest_provider" {
  description = "Encryption at rest provider (null if NONE)"
  value       = module.cluster_import.encryption_at_rest_provider
}

output "version_release_system" {
  description = "Version release system (LTS or CONTINUOUS)"
  value       = module.cluster_import.version_release_system
}

output "replica_set_scaling_strategy" {
  description = "Replica set scaling strategy"
  value       = module.cluster_import.replica_set_scaling_strategy
}

output "global_cluster_self_managed_sharding" {
  description = "Global cluster self-managed sharding"
  value       = module.cluster_import.global_cluster_self_managed_sharding
}

output "advanced_configuration" {
  description = "Advanced configuration settings (null if all match defaults)"
  value       = module.cluster_import.advanced_configuration
}

output "bi_connector_config" {
  description = "BI Connector configuration (null if disabled)"
  value       = module.cluster_import.bi_connector_config
}

# Summary output for easy review
output "summary" {
  description = "Human-readable summary of the cluster configuration"
  value       = module.cluster_import.summary
}

# Generated Terraform file content
output "terraform_file_content" {
  description = "Complete .tf file content ready to save as {cluster_name}.tf"
  value       = local.terraform_file_content
}

output "terraform_filename" {
  description = "Suggested filename for the generated terraform file"
  value       = "${module.cluster_import.name}.tf"
}
