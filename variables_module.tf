## CONDITIONAL RESOURCES
variable "search_deployment_enabled" {
  type    = bool
  default = false
}

variable "search_deployment" {
  type = object({
    specs = list(object({
      instance_size = string
      node_count    = number
    }))
    delete_on_create_timeout = optional(bool, true)
    skip_wait_on_update      = optional(bool, false)
    timeouts = optional(object({
      create = optional(string)
      delete = optional(string)
      update = optional(string)
    }))
  })
  nullable = true
  default  = null
}

variable "cloud_backup_schedule_enabled" {
  type    = bool
  default = false
}

# duplicate of the one in modules/cloud_backup_schedule/variables.tf
variable "cloud_backup_schedule" {
  type = object({
    auto_export_enabled                      = optional(bool)
    reference_hour_of_day                    = optional(number)
    reference_minute_of_hour                 = optional(number)
    restore_window_days                      = optional(number)
    update_snapshots                         = optional(bool)
    use_org_and_group_names_in_export_prefix = optional(bool)
    copy_settings = optional(list(object({
      cloud_provider     = optional(string) # "AWS" | "GCP" | "AZURE"
      frequencies        = optional(list(string))
      region_name        = optional(string)
      should_copy_oplogs = optional(bool)
      zone_id            = optional(string)
    })))
    export = optional(list(object({
      export_bucket_id = optional(string)
      frequency_type   = optional(string)
    })))
    policy_item_daily = optional(list(object({
      frequency_interval = number
      retention_unit     = string
      retention_value    = number
    })))
    policy_item_hourly = optional(list(object({
      frequency_interval = number
      retention_unit     = string
      retention_value    = number
    })))
    policy_item_monthly = optional(list(object({
      frequency_interval = number
      retention_unit     = string
      retention_value    = number
    })))
    policy_item_weekly = optional(list(object({
      frequency_interval = number
      retention_unit     = string
      retention_value    = number
    })))
    policy_item_yearly = optional(list(object({
      frequency_interval = number
      retention_unit     = string
      retention_value    = number
    })))
  })
  nullable = true
  default  = null
}

## CLUSTER

variable "name" {
  description = "Human-readable label that identifies this cluster."
  type        = string
  default     = ""
}

variable "name_prefix" {
  description = "Prefix for the cluster name if not specified in the `name` variable."
  type        = string
  default     = "lz-module-"
}

variable "regions" {
  description = <<-EOT
The simplest way to define your cluster topology.
By default REPLICASET cluster.
Use `shard_index` for SHARDED cluster.
Use `zone_name` for GEOSHARDED cluster.

EOT

  type = list(object({
    name                    = optional(string)
    node_count              = optional(number)
    shard_index             = optional(number)
    provider_name           = optional(string)
    node_count_read_only    = optional(number)
    node_count_analytics    = optional(number)
    instance_size           = optional(string)
    instance_size_analytics = optional(string)
    zone_name               = optional(string)
  }))
}

variable "provider_name" {
  description = "AWS/AZURE/GCP, setting this on the root level, will use it inside of each `region`"
  type        = string
  nullable    = true
  default     = null
}

variable "instance_size" {
  description = "Default instance_size in electable/read-only specs. Only used when auto_scaling.compute_enabled = false. Defaults to M10 if not specified."
  type        = string
  nullable    = true
  default     = null
}

variable "disk_size_gb" {
  description = <<-EOT
Storage capacity of instance data volumes expressed in gigabytes. Increase this number to add capacity.

 This value must be equal for all shards and node types.

 This value is not configurable on M0/M2/M5 clusters.

 MongoDB Cloud requires this parameter if you set **replicationSpecs**.

 If you specify a disk size below the minimum (10 GB), this parameter defaults to the minimum disk size value. 

 Storage charge calculations depend on whether you choose the default value or a custom value.

 The maximum value for disk storage cannot exceed 50 times the maximum RAM for the selected cluster. If you require more storage space, consider upgrading your cluster to a higher tier.
EOT

  type     = number
  nullable = true
  default  = null
}

variable "instance_size_analytics" {
  description = "Default instance_size in analytics specs. Do not set if using auto_scaling_analytics."
  type        = string
  nullable    = true
  default     = null
}

variable "auto_scaling" {
  description = "Auto scaling config for electable/read-only specs. Enabled by default with Architecture Center recommended defaults."
  type = object({
    compute_enabled            = optional(bool, true)
    compute_max_instance_size  = optional(string, "M60")
    compute_min_instance_size  = optional(string, "M30")
    compute_scale_down_enabled = optional(bool, true)
    disk_gb_enabled            = optional(bool, true)
  })
  nullable = true
  default = {
    compute_enabled            = true
    compute_max_instance_size  = "M60"
    compute_min_instance_size  = "M30"
    compute_scale_down_enabled = true
    disk_gb_enabled            = true
  }
}

variable "auto_scaling_analytics" {
  description = "Auto scaling config for analytics specs."
  type = object({
    compute_enabled            = optional(bool)
    compute_max_instance_size  = optional(string)
    compute_min_instance_size  = optional(string)
    compute_scale_down_enabled = optional(bool)
    disk_gb_enabled            = optional(bool)
  })
  nullable = true
  default  = null
}

variable "tags_required" {
  description = "List of required tag keys for enterprise compliance. Default matches Architecture Center recommendations."
  type        = list(string)
  default = [
    "department",
    "team",
    "application",
    "environment",
    "version",
    "email",
    "criticality"
  ]
}

variable "tags" {
  description = "Map that contains key-value pairs between 1 to 255 characters in length for tagging and categorizing the cluster."
  type        = map(string)
  default     = {}
}
