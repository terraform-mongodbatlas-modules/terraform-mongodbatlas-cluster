variable "name" {
  description = "Human-readable label that identifies this cluster, for example: `my-product-cluster`."
  type        = string
}

variable "regions" {
  description = <<-EOT
The simplest way to define your cluster topology:
- Set `name`, for example `US_EAST_1`, see all valid [region names](https://www.mongodb.com/docs/atlas/cloud-providers-regions/).
- Set `node_count`, `node_count_read_only`, `node_count_analytics` depending on your needs.
- Set `provider_name` (AWS/AZURE/GCP) or use the "root" level `provider_name` variable if all regions share the provider_name.
- For cluster_type.REPLICASET: omit both `shard_number` and `zone_name`.
- For cluster_type.SHARDED: set `shard_number` on each region or use the `shard_count` variable; do not set `zone_name`. Regions with the same `shard_number` belong to the same shard.
- For cluster_type.GEOSHARDED: set `zone_name` on each region; optionally set `shard_number`. Regions with the same `zone_name` form one zone.

NOTE:
- The order in which region blocks are defined in this list determines their priority within each shard or zone.
  - The first region gets priority 7 (maximum), the next 6, and so on (minimum 0). For more context, see [this section of the Atlas Admin API documentation](https://www.mongodb.com/docs/api/doc/atlas-admin-api-v2/operation/operation-creategroupcluster#operation-creategroupcluster-body-application-vnd-atlas-2024-10-23-json-replicationspecs-regionconfigs-priority).
- Within a zone, shard_numbers are specific to that zone and independent of the shard_number in any other zones.
- `shard_number` is a variable specific to this module used to group regions within a shard and does not represent an actual value in Atlas.
EOT
  type = list(object({
    name                    = string
    disk_iops               = optional(number)
    disk_size_gb            = optional(number)
    ebs_volume_type         = optional(string)
    instance_size           = optional(string)
    instance_size_analytics = optional(string)
    node_count              = optional(number)
    node_count_analytics    = optional(number)
    node_count_read_only    = optional(number)
    provider_name           = optional(string)
    shard_number            = optional(number)
    zone_name               = optional(string)
  }))

  validation {
    error_message = "Only provider_name AWS/AZURE/GCP are allowed."
    condition     = length([for region in var.regions : region if region.provider_name != null && !contains(["AWS", "AZURE", "GCP"], coalesce(region.provider_name, "AWS"))]) == 0 # (1) coalesce avoids `Invalid value for "value" parameter: argument must not be null.` in terraform CLI 1.11 and earlier (2) using `AWS` as default since a null value is OK (notice ! before contains)
  }

  validation {
    error_message = "M0, M2, and M5 are not allowed for this module. Use M10 or higher instead."
    condition     = length([for region in var.regions : region if region.instance_size != null && (region.instance_size == "M0" || region.instance_size == "M2" || region.instance_size == "M5")]) == 0
  }

  validation {
    error_message = "no node count specified at indexes ${join(",", [for idx, region in var.regions : idx if alltrue([region.node_count == null, region.node_count_read_only == null, region.node_count_analytics == null])])}"
    condition     = length([for idx, region in var.regions : idx if alltrue([region.node_count == null, region.node_count_read_only == null, region.node_count_analytics == null])]) == 0
  }
  validation {
    condition = alltrue([
      for r in var.regions :
      (
        r.shard_number == null
        || try(r.shard_number == floor(r.shard_number) && r.shard_number >= 0, false)
      )
    ])
    error_message = "Each regions[*].shard_number must be a non-negative whole integer (e.g., 0, 1, 2...) if provided."
  }
}

variable "provider_name" {
  description = "AWS/AZURE/GCP, setting this on the root level, will use it inside of each `region`."
  type        = string
  nullable    = true
  default     = null

  validation {
    error_message = "Only provider_name AWS/AZURE/GCP are allowed."
    condition     = var.provider_name == null || contains(["AWS", "AZURE", "GCP"], coalesce(var.provider_name, "empty")) # coalesce avoids `Invalid value for "value" parameter: argument must not be null.` in terraform CLI 1.11 and earlier
  }
}

variable "instance_size" {
  description = "Default instance_size in electable/read-only specs. Only used when auto_scaling.compute_enabled = false. Defaults to M10 if not specified."
  type        = string
  nullable    = true
  default     = null

  validation {
    error_message = "M0, M2, and M5 are not allowed for this module. Use M10 or higher instead."
    condition     = var.instance_size == null || (var.instance_size != "M0" && var.instance_size != "M2" && var.instance_size != "M5")
  }
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

variable "disk_iops" {
  type        = number
  description = <<-EOT
Only valid for AWS and Azure instances.

#### AWS
Target IOPS (Input/Output Operations Per Second) desired for storage attached to this hardware.

Change this parameter if you:

- set `"replicationSpecs[n].regionConfigs[m].providerName" to "AWS"`.
- set `"replicationSpecs[n].regionConfigs[m].electableSpecs.instanceSize" to "M30"` or greater (not including `Mxx_NVME` tiers).

- set `"replicationSpecs[n].regionConfigs[m].electableSpecs.ebsVolumeType" to "PROVISIONED"`.

The maximum input/output operations per second (IOPS) depend on the selected **.instanceSize** and **.diskSizeGB**.
This parameter defaults to the cluster tier's standard IOPS value.
Changing this value impacts cluster cost.
MongoDB Cloud enforces minimum ratios of storage capacity to system memory for given cluster tiers. This keeps cluster performance consistent with large datasets.

- Instance sizes `M10` to `M40` have a ratio of disk capacity to system memory of 60:1.
- Instance sizes greater than `M40` have a ratio of 120:1.

#### Azure
Target throughput desired for storage attached to your Azure-provisioned cluster. Change this parameter if you:

- set `"replicationSpecs[n].regionConfigs[m].providerName" : "Azure"`.
- set `"replicationSpecs[n].regionConfigs[m].electableSpecs.instanceSize" : "M40"` or greater not including `Mxx_NVME` tiers.

The maximum input/output operations per second (IOPS) depend on the selected **.instanceSize** and **.diskSizeGB**.
This parameter defaults to the cluster tier's standard IOPS value.
Changing this value impacts cluster cost.
EOT
  nullable    = true
  default     = null
}

variable "ebs_volume_type" {
  type        = string
  nullable    = true
  default     = null
  description = <<-EOT
Type of storage you want to attach to your AWS-provisioned cluster.\n\n- `STANDARD` volume types can't exceed the default input/output operations per second (IOPS) rate for the selected volume size. \n\n- `PROVISIONED` volume types must fall within the allowable IOPS range for the selected volume size. You must set this value to (`PROVISIONED`) for NVMe clusters.
EOT
}


variable "instance_size_analytics" {
  description = "Default instance_size in analytics specs. Do not set if using auto_scaling_analytics."
  type        = string
  nullable    = true
  default     = null
  validation {
    error_message = "M0, M2, and M5 are not allowed for this module. Use M10 or higher instead."
    condition     = var.instance_size_analytics == null || (var.instance_size_analytics != "M0" && var.instance_size_analytics != "M2" && var.instance_size_analytics != "M5")
  }
}

variable "auto_scaling" {
  description = "Auto scaling config for electable/read-only specs. Enabled by default with Architecture Center recommended defaults."
  type = object({
    compute_enabled            = optional(bool, true)
    compute_max_instance_size  = optional(string, "M200")
    compute_min_instance_size  = optional(string, "M10")
    compute_scale_down_enabled = optional(bool, true)
    disk_gb_enabled            = optional(bool, true)
  })

  default = {
    compute_enabled            = true
    compute_max_instance_size  = "M200"
    compute_min_instance_size  = "M10"
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
  description = <<-EOT
Number of shards for SHARDED clusters.

- When set, all shards share the same region topology (each shard gets the same regions list).
- Do NOT set regions[*].shard_number when shard_count is set (they are mutually exclusive).
- When unset, you must set regions[*].shard_number on every region to explicitly group regions into shards.

EOT
  type        = number
  nullable    = true
  default     = null

  validation {
    condition     = var.shard_count == null || try(var.shard_count == floor(var.shard_count) && var.shard_count >= 1, false)
    error_message = "shard_count must be ≥ 1 if set."
  }

  validation {
    condition     = var.shard_count == null || var.cluster_type == "SHARDED"
    error_message = "shard_count can only be set when cluster_type is SHARDED."
  }
}
