variable "cluster_size" {
  type    = string
  default = ""

  validation {
    condition     = var.cluster_size == "" || contains(keys(local.sizes), var.cluster_size)
    error_message = "size=${var.cluster_size} not found in ${join(",", keys(local.sizes))}"
  }
}

variable "shards" {
  type    = number
  default = 0
}

variable "regions_names" {
  type        = list(string)
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
    shards = number
  }))
  default = {}
}
