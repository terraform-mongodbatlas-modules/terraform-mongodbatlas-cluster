variable "name" {
  description = "Human-readable label that identifies this cluster."
  type        = string
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

variable "tags" {
  description = "Map that contains key-value pairs between 1 to 255 characters in length for tagging and categorizing the cluster."
  type        = map(string)
  default     = {}
}
