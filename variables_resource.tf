variable "accept_data_risks_and_force_replica_set_reconfig" {
  description = <<-EOT
If reconfiguration is necessary to regain a primary due to a regional outage, submit this field alongside your topology reconfiguration to request a new regional outage resistant topology.

Forced reconfigurations during an outage of the majority of electable nodes carry a risk of data loss if replicated writes (even majority committed writes) have not been replicated to the new primary node. See [Replication](https://www.mongodb.com/docs/manual/replication/) in the MongoDB Atlas documentation for more information. To proceed with an operation which carries that risk, set `accept_data_risks_and_force_replica_set_reconfig` to the current date.
EOT
  type        = string
  nullable    = true
  default     = null
}

variable "advanced_configuration" {
  description = "Additional settings for an Atlas cluster."
  type = object({
    change_stream_options_pre_and_post_images_expire_after_seconds = optional(number)
    custom_openssl_cipher_config_tls12                             = optional(list(string))
    default_max_time_ms                                            = optional(number)
    default_write_concern                                          = optional(string, "majority")
    javascript_enabled                                             = optional(bool, false)
    minimum_enabled_tls_protocol                                   = optional(string, "TLS1_2")
    no_table_scan                                                  = optional(bool)
    oplog_min_retention_hours                                      = optional(number)
    oplog_size_mb                                                  = optional(number)
    sample_refresh_interval_bi_connector                           = optional(number)
    sample_size_bi_connector                                       = optional(number)
    tls_cipher_config_mode                                         = optional(string)
    transaction_lifetime_limit_seconds                             = optional(number)
  })
  nullable = true
  default = {
    default_write_concern        = "majority"
    javascript_enabled           = false
    minimum_enabled_tls_protocol = "TLS1_2"
  }
}

variable "backup_enabled" {
  description = "Recommended for production clusters. Flag that indicates whether the cluster can perform backups. If set to `true`, the cluster can perform backups; if set to `false`, the cluster doesn't use backups. You must set this value to `true` for NVMe clusters. Backup uses [Cloud Backups](https://docs.atlas.mongodb.com/backup/cloud-backup/overview/) for dedicated clusters and [Shared Cluster Backups](https://docs.atlas.mongodb.com/backup/shared-tier/overview/) for tenant clusters."
  type        = bool
  default     = true
}

variable "bi_connector_config" {
  description = "Setting needed to configure the MongoDB Connector for Business Intelligence for this cluster."
  type = object({
    enabled         = optional(bool)
    read_preference = optional(string)
  })
  nullable = true
  default  = null
}

variable "cluster_type" {
  description = "Type of the cluster that you want to create. Valid values are `REPLICASET` / `SHARDED` / `GEOSHARDED`."
  type        = string

  validation {
    condition     = contains(["REPLICASET", "SHARDED", "GEOSHARDED"], var.cluster_type)
    error_message = "Invalid cluster type. Valid values are REPLICASET, SHARDED, GEOSHARDED."
  }
}

variable "config_server_management_mode" {
  description = <<-EOT
Config Server Management Mode for creating or updating a sharded cluster.

When configured as `ATLAS_MANAGED`, Atlas may automatically switch the cluster's config server type for optimal performance and savings.

When configured as `FIXED_TO_DEDICATED`, the cluster always uses a dedicated config server.
EOT

  type     = string
  nullable = true
  default  = null
}

variable "delete_on_create_timeout" {
  description = "Flag that indicates whether to delete the cluster if the cluster creation times out. Default is false."
  type        = bool
  nullable    = true
  default     = null
}

variable "encryption_at_rest_provider" {
  description = "Cloud service provider that manages your customer keys to provide an additional layer of encryption at rest for the cluster. To enable customer key management for encryption at rest, the cluster **replication_specs[n].region_configs[m].{type}_specs.instance_size** setting must be `M10` or higher and `\"backup_enabled\" : false` or omitted entirely."
  type        = string
  nullable    = true
  default     = null
}

variable "global_cluster_self_managed_sharding" {
  description = <<-EOT
Set this field to configure the Sharding Management Mode when creating a new Global Cluster.

When set to false, the management mode is set to Atlas-Managed Sharding. This mode fully manages the sharding of your Global Cluster and is built to provide a seamless deployment experience.

When set to true, the management mode is set to Self-Managed Sharding. This mode leaves the management of shards in your hands and is built to provide an advanced and flexible deployment experience.

*Important*: This setting cannot be changed once the cluster is deployed.
EOT

  type     = bool
  nullable = true
  default  = null
}

variable "mongo_db_major_version" {
  description = <<-EOT
MongoDB major version of the cluster.

On creation: Choose from the available versions of MongoDB, or leave unspecified for the current recommended default in the MongoDB Cloud platform. The recommended version is a recent Long Term Support version. The default is not guaranteed to be the most recently released version throughout the entire release cycle. For versions available in a specific project, see the linked documentation or use the API endpoint for [project LTS versions endpoint](#tag/Projects/operation/getProjectLTSVersions).

 On update: Increase version only by one major version at a time. If the cluster is pinned to a MongoDB feature compatibility version exactly one major version below the current MongoDB version, you can downgrade to the previous MongoDB major version.
EOT

  type     = string
  nullable = true
  default  = null
}

variable "paused" {
  description = "Flag that indicates whether the cluster is paused."
  type        = bool
  nullable    = true
  default     = null
}

variable "pinned_fcv" {
  description = "Pins the Feature Compatibility Version (FCV) to the current MongoDB version with a provided expiration date. To unpin the FCV, the `pinned_fcv` attribute must be removed. This operation can take several minutes as the request processes through the MongoDB data plane. Once FCV is unpinned it will not be possible to downgrade the `mongo_db_major_version`. We recommend updating to `pinned_fcv` in isolation from other cluster changes. If a plan contains multiple changes, the FCV change will be applied first. If FCV is unpinned past the expiration date the `pinned_fcv` attribute must be removed. See the following [knowledge hub article](https://kb.corp.mongodb.com/article/000021785/) and the [FCV documentation](https://www.mongodb.com/docs/atlas/tutorial/major-version-change/#manage-feature-compatibility--fcv--during-upgrades) for more details."
  type = object({
    expiration_date = string
  })
  nullable = true
  default  = null
}

variable "pit_enabled" {
  description = "Recommended for production clusters. Flag that indicates whether the cluster uses continuous cloud backups."
  type        = bool
  nullable    = false
  default     = true
}

variable "project_id" {
  description = <<-EOT
Unique 24-hexadecimal digit string that identifies your project, for example `664619d870c247237f4b86a6`. It is found listing projects in the Admin API or selecting a project in the UI and copying the path in the URL.

**NOTE**: Groups and projects are synonymous terms. Your group id is the same as your project id. For existing groups, your group/project id remains the same. The resource and corresponding endpoints use the term groups.
EOT

  type = string
}

variable "redact_client_log_data" {
  description = <<-EOT
Enable or disable log redaction.

This setting configures the ``mongod`` or ``mongos`` to redact any document field contents from a message accompanying a given log event before logging. This prevents the program from writing potentially sensitive data stored on the database to the diagnostic log. Metadata such as error or operation codes, line numbers, and source file names are still visible in the logs.

Use ``redact_client_log_data`` in conjunction with Encryption at Rest and TLS/SSL (Transport Encryption) to assist compliance with regulatory requirements.

*Note*: Changing this setting on a cluster will trigger a rolling restart as soon as the cluster is updated.
EOT

  type     = bool
  nullable = true
  default  = true # changed
}

variable "replica_set_scaling_strategy" {
  description = <<-EOT
Set this field to configure the replica set scaling mode for your cluster.

By default, Atlas scales under `WORKLOAD_TYPE`. This mode allows Atlas to scale your analytics nodes in parallel to your operational nodes.

When configured as `SEQUENTIAL`, Atlas scales all nodes sequentially. This mode is intended for steady-state workloads and applications performing latency-sensitive secondary reads.
EOT

  type     = string
  nullable = true
  default  = null
}

variable "replication_specs" {
  description = "List of settings that configure your cluster regions. This array has one object per shard representing node configurations in each shard. For replica sets there is only one object representing node configurations."
  type = list(object({
    region_configs = list(object({
      analytics_auto_scaling = optional(object({
        compute_enabled            = optional(bool)
        compute_max_instance_size  = optional(string)
        compute_min_instance_size  = optional(string)
        compute_scale_down_enabled = optional(bool)
        disk_gb_enabled            = optional(bool)
      }))
      analytics_specs = optional(object({
        disk_iops       = optional(number)
        disk_size_gb    = optional(number)
        ebs_volume_type = optional(string)
        instance_size   = optional(string)
        node_count      = optional(number)
      }))
      auto_scaling = optional(object({
        compute_enabled            = optional(bool)
        compute_max_instance_size  = optional(string)
        compute_min_instance_size  = optional(string)
        compute_scale_down_enabled = optional(bool)
        disk_gb_enabled            = optional(bool)
      }))
      backing_provider_name = optional(string)
      electable_specs = optional(object({
        disk_iops       = optional(number)
        disk_size_gb    = optional(number)
        ebs_volume_type = optional(string)
        instance_size   = optional(string)
        node_count      = optional(number)
      }))
      priority      = number
      provider_name = string
      read_only_specs = optional(object({
        disk_iops       = optional(number)
        disk_size_gb    = optional(number)
        ebs_volume_type = optional(string)
        instance_size   = optional(string)
        node_count      = optional(number)
      }))
      region_name = string
    }))
    zone_name = optional(string)
  }))
  default = []

  validation {
    condition = alltrue([
      for spec in var.replication_specs : alltrue([
        for region_config in spec.region_configs :
        (region_config.auto_scaling == null || region_config.auto_scaling.compute_enabled == false) && (region_config.analytics_auto_scaling == null || region_config.analytics_auto_scaling.compute_enabled == false)
      ])
    ])
    error_message = "This module doesn't support `auto_scaling` for `replication_specs` variable, please use `regions` and `auto_scaling` variables instead."
  }

  validation {
    # var.auto_scaling should be the default value for the auto_scaling variable
    condition = length(var.replication_specs) == 0 || var.auto_scaling == {
      compute_enabled            = true
      compute_max_instance_size  = "M200"
      compute_min_instance_size  = "M10"
      compute_scale_down_enabled = true
      disk_gb_enabled            = true
    }

    error_message = "Cannot use `var.auto_scaling` when `var.replication_specs` is used. Configure `auto_scaling` within `replication_specs[*].region_configs[*].auto_scaling` instead."
  }

  validation {
    condition     = length(var.replication_specs) == 0 || var.auto_scaling_analytics == null
    error_message = "Cannot use `var.auto_scaling_analytics` when `var.replication_specs` is used. Configure `auto_scaling_analytics` within `replication_specs[*].region_configs[*].analytics_auto_scaling` instead."
  }

  validation {
    condition     = length(var.replication_specs) == 0 || var.instance_size == null
    error_message = "Cannot use `var.instance_size` when `var.replication_specs` is used. Configure `instance_size` within `replication_specs[*].region_configs[*].electable_specs.instance_size` or `read_only_specs.instance_size` instead."
  }

  validation {
    condition     = length(var.replication_specs) == 0 || var.instance_size_analytics == null
    error_message = "Cannot use `var.instance_size_analytics` when `var.replication_specs` is used. Configure `instance_size` within `replication_specs[*].region_configs[*].analytics_specs.instance_size` instead."
  }

  validation {
    condition     = length(var.replication_specs) == 0 || var.disk_iops == null
    error_message = "Cannot use `var.disk_iops` when `var.replication_specs` is used. Configure `disk_iops` within `replication_specs[*].region_configs[*].electable_specs.disk_iops`, `read_only_specs.disk_iops`, or `analytics_specs.disk_iops` instead."
  }

  validation {
    condition     = length(var.replication_specs) == 0 || var.disk_size_gb == null
    error_message = "Cannot use `var.disk_size_gb` when `var.replication_specs` is used. Configure `disk_size_gb` within `replication_specs[*].region_configs[*].electable_specs.disk_size_gb`, `read_only_specs.disk_size_gb`, or `analytics_specs.disk_size_gb` instead."
  }

  validation {
    condition     = length(var.replication_specs) == 0 || var.ebs_volume_type == null
    error_message = "Cannot use `var.ebs_volume_type` when `var.replication_specs` is used. Configure `ebs_volume_type` within `replication_specs[*].region_configs[*].electable_specs.ebs_volume_type`, `read_only_specs.ebs_volume_type`, or `analytics_specs.ebs_volume_type` instead."
  }

  validation {
    condition     = length(var.replication_specs) == 0 || var.shard_count == null
    error_message = "Cannot use `var.shard_count` when `var.replication_specs` is used. Shard configuration is defined by the number of `replication_specs` provided."
  }

  validation {
    condition     = length(var.replication_specs) == 0 || var.provider_name == null
    error_message = "Cannot use `var.provider_name` when `var.replication_specs` is used. Configure `provider_name` within `replication_specs[*].region_configs[*].provider_name` instead."
  }
}

variable "retain_backups_enabled" {
  description = "Recommended for production clusters. Flag that indicates whether to retain backup snapshots for the deleted dedicated cluster."
  type        = bool
  default     = true
}

variable "root_cert_type" {
  description = "Root Certificate Authority that MongoDB Cloud cluster uses. MongoDB Cloud supports Internet Security Research Group."
  type        = string
  nullable    = true
  default     = null
}

variable "termination_protection_enabled" {
  description = "Recommended for production clusters. Flag that indicates whether termination protection is enabled on the cluster. If set to `true`, MongoDB Cloud does not delete the cluster; if set to `false`, MongoDB Cloud deletes the cluster."
  type        = bool
  nullable    = true
  default     = null
}

variable "timeouts" {
  description = "Timeouts for `create`, `update`, and `delete` operations."
  type = object({
    create = optional(string)
    delete = optional(string)
    update = optional(string)
  })
  nullable = true
  default  = null
}

variable "version_release_system" {
  description = "Method by which the cluster maintains the MongoDB versions. If value is `CONTINUOUS`, you must not specify `mongo_db_major_version*`."
  type        = string
  nullable    = true
  default     = null
}
