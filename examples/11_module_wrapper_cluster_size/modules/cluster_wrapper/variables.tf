
variable "cluster_size" {
  type    = string
  default = ""

  validation {
    condition     = var.cluster_size == "" || contains(keys(local.sizes), var.cluster_size)
    error_message = "size=${var.cluster_size} not found in ${join(",", keys(local.sizes))}"
  }
}

variable "regions_names" {
  type = list(string)
  # Company preferred regions, can be overwritten
  default     = ["US_EAST_1", "EU_WEST_2", "AP_SOUTHEAST_1"]
  description = "Atlas Regions used in cluster"
}

variable "region_extra" {
  type = object({
    provider_name           = optional(string)
    instance_size           = optional(string)
    instance_size_analytics = optional(string)
  })
  default     = {}
  description = "use this to merge defaults (not used by zones)"
}

variable "zones" {
  type = map(object({
    regions = list(object({
      name                    = string
      node_count              = optional(number)
      node_count_read_only    = optional(number)
      node_count_analytics    = optional(number)
      provider_name           = optional(string)
      instance_size           = optional(string)
      instance_size_analytics = optional(string)
    }))
    shard_count = number
  }))
  default = {}
}

## Passthrough variables for the cluster module
variable "name" {
  description = "Human-readable label that identifies this cluster, for example: `my-product-cluster`."
  type        = string
}

variable "cluster_type" {
  description = "Type of the cluster that you want to create. Valid values are REPLICASET/SHARDED/GEOSHARDED."
  type        = string

  validation {
    condition     = contains(["REPLICASET", "SHARDED", "GEOSHARDED"], var.cluster_type)
    error_message = "Invalid cluster type. Valid values are REPLICASET, SHARDED, GEOSHARDED."
  }
}

variable "project_id" {
  description = <<-EOT
Unique 24-hexadecimal digit string that identifies your project, for example `664619d870c247237f4b86a6`. It is found listing projects in the Admin API or selecting a project in the UI and copying the path in the URL.

**NOTE**: Groups and projects are synonymous terms. Your group id is the same as your project id. For existing groups, your group/project id remains the same. The resource and corresponding endpoints use the term groups.
EOT

  type = string
}

variable "tags" {
  description = <<-EOT
Map that contains key-value pairs between 1 to 255 characters in length for tagging and categorizing the cluster.
We recommend setting:
Department, team name, application name, environment, version, email contact, criticality. 
These values can be used for:
- Billing.
- Data classification.
- Regional compliance requirements for audit and governance purposes.
EOT
  type        = map(string)
  default     = {}
}

variable "shard_count" {
  type     = number
  default  = null
  nullable = true
}
