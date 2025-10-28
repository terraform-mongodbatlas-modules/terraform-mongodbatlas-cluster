# Use the submodule to perform the cluster import transformation

terraform {
  required_version = ">= 1.6"
  required_providers {
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "~> 2.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "2.4.1"
    }
  }
}

provider "mongodbatlas" {}
variable "project_id" {
  description = "MongoDB Atlas Project ID"
  type        = string
}

data "mongodbatlas_advanced_clusters" "this" {
  project_id = var.project_id
}

module "cluster_import" {
  source  = "./modules/cluster_import"
  cluster = data.mongodbatlas_advanced_clusters.this.results[0]
}

locals {
  # Helper to format HCL values
  format_value = {
    string      = "  %s = %q\n"
    number      = "  %s = %v\n"
    bool        = "  %s = %v\n"
    string_list = "  %s = %s\n"
    map         = "  %s = %s\n"
  }

  # Format regions list - only include non-null values
  regions_hcl = join("", [
    for region in module.cluster_import.regions :
    <<-EOT
    {
      name          = ${format("%q", region.name)}${region.provider_name != null ? format("\n      provider_name = %q", region.provider_name) : ""}${region.node_count != null ? format("\n      node_count    = %v", region.node_count) : ""}${region.node_count_read_only != null ? format("\n      node_count_read_only = %v", region.node_count_read_only) : ""}${region.node_count_analytics != null ? format("\n      node_count_analytics = %v", region.node_count_analytics) : ""}${region.instance_size != null ? format("\n      instance_size = %q", region.instance_size) : ""}${region.instance_size_analytics != null ? format("\n      instance_size_analytics = %q", region.instance_size_analytics) : ""}${region.disk_size_gb != null ? format("\n      disk_size_gb  = %v", region.disk_size_gb) : ""}${region.disk_iops != null ? format("\n      disk_iops     = %v", region.disk_iops) : ""}${region.ebs_volume_type != null ? format("\n      ebs_volume_type = %q", region.ebs_volume_type) : ""}${region.shard_number != null ? format("\n      shard_number  = %v", region.shard_number) : ""}${region.zone_name != null ? format("\n      zone_name     = %q", region.zone_name) : ""}
    },
    EOT
  ])

  # Format auto_scaling block as proper HCL
  auto_scaling_hcl = module.cluster_import.auto_scaling != null ? "\n\n  auto_scaling = {\n    compute_enabled            = ${module.cluster_import.auto_scaling.compute_enabled}${module.cluster_import.auto_scaling.compute_max_instance_size != null ? format("\n    compute_max_instance_size  = %q", module.cluster_import.auto_scaling.compute_max_instance_size) : ""}${module.cluster_import.auto_scaling.compute_min_instance_size != null ? format("\n    compute_min_instance_size  = %q", module.cluster_import.auto_scaling.compute_min_instance_size) : ""}\n    compute_scale_down_enabled = ${module.cluster_import.auto_scaling.compute_scale_down_enabled}\n    disk_gb_enabled            = ${module.cluster_import.auto_scaling.disk_gb_enabled}\n  }" : ""

  # Format auto_scaling_analytics block as proper HCL
  auto_scaling_analytics_hcl = module.cluster_import.auto_scaling_analytics != null ? "\n\n  auto_scaling_analytics = {\n    compute_enabled            = ${module.cluster_import.auto_scaling_analytics.compute_enabled}${module.cluster_import.auto_scaling_analytics.compute_max_instance_size != null ? format("\n    compute_max_instance_size  = %q", module.cluster_import.auto_scaling_analytics.compute_max_instance_size) : ""}${module.cluster_import.auto_scaling_analytics.compute_min_instance_size != null ? format("\n    compute_min_instance_size  = %q", module.cluster_import.auto_scaling_analytics.compute_min_instance_size) : ""}\n    compute_scale_down_enabled = ${module.cluster_import.auto_scaling_analytics.compute_scale_down_enabled}\n    disk_gb_enabled            = ${module.cluster_import.auto_scaling_analytics.disk_gb_enabled}\n  }" : ""

  # Generate the complete .tf file content
  terraform_file_content = <<-EOT
# Auto-generated from existing cluster: ${module.cluster_import.name}
# Cluster Type: ${module.cluster_import.cluster_type}
# Generated: ${timestamp()}

module "${replace(module.cluster_import.name, "-", "_")}" {
  source = "../../"  # Adjust path to your cluster module

  project_id = var.project_id

  name = ${format("%q", module.cluster_import.name)}
  
  cluster_type = ${format("%q", module.cluster_import.cluster_type)}

  regions = [
${local.regions_hcl}  ]
${module.cluster_import.provider_name != null ? format("\n  provider_name = %q", module.cluster_import.provider_name) : ""}${module.cluster_import.instance_size != null ? format("\n  instance_size = %q", module.cluster_import.instance_size) : ""}${module.cluster_import.disk_size_gb != null ? format("\n  disk_size_gb  = %v", module.cluster_import.disk_size_gb) : ""}${module.cluster_import.disk_iops != null ? format("\n  disk_iops     = %v", module.cluster_import.disk_iops) : ""}${module.cluster_import.ebs_volume_type != null ? format("\n  ebs_volume_type = %q", module.cluster_import.ebs_volume_type) : ""}${module.cluster_import.instance_size_analytics != null ? format("\n  instance_size_analytics = %q", module.cluster_import.instance_size_analytics) : ""}${module.cluster_import.shard_count != null ? format("\n  shard_count = %v", module.cluster_import.shard_count) : ""}${module.cluster_import.mongo_db_major_version != null ? format("\n  mongo_db_major_version = %q", module.cluster_import.mongo_db_major_version) : ""}${module.cluster_import.backup_enabled != null ? format("\n  backup_enabled = %v", module.cluster_import.backup_enabled) : ""}${module.cluster_import.pit_enabled != null ? format("\n  pit_enabled = %v", module.cluster_import.pit_enabled) : ""}${module.cluster_import.termination_protection_enabled != null ? format("\n  termination_protection_enabled = %v", module.cluster_import.termination_protection_enabled) : ""}${module.cluster_import.redact_client_log_data != null ? format("\n  redact_client_log_data = %v", module.cluster_import.redact_client_log_data) : ""}${module.cluster_import.encryption_at_rest_provider != null ? format("\n  encryption_at_rest_provider = %q", module.cluster_import.encryption_at_rest_provider) : ""}${module.cluster_import.version_release_system != null ? format("\n  version_release_system = %q", module.cluster_import.version_release_system) : ""}${module.cluster_import.replica_set_scaling_strategy != null ? format("\n  replica_set_scaling_strategy = %q", module.cluster_import.replica_set_scaling_strategy) : ""}${module.cluster_import.global_cluster_self_managed_sharding != null ? format("\n  global_cluster_self_managed_sharding = %v", module.cluster_import.global_cluster_self_managed_sharding) : ""}${module.cluster_import.tags != null ? format("\n  tags = %s", jsonencode(module.cluster_import.tags)) : ""}${local.auto_scaling_hcl}${local.auto_scaling_analytics_hcl}${module.cluster_import.advanced_configuration != null ? format("\n\n  advanced_configuration = %s", jsonencode(module.cluster_import.advanced_configuration)) : ""}${module.cluster_import.bi_connector_config != null ? format("\n\n  bi_connector_config = %s", jsonencode(module.cluster_import.bi_connector_config)) : ""}
}

# Outputs
output "${replace(module.cluster_import.name, "-", "_")}_connection_strings" {
  description = "Connection strings for ${module.cluster_import.name}"
  value       = module.${replace(module.cluster_import.name, "-", "_")}.connection_strings
}
EOT
}

resource "local_file" "cluster_out" {
  content  = local.terraform_file_content
  filename = "${module.cluster_import.name}.tf"
}
