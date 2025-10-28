variable "cluster" {
  description = "Cluster object from mongodbatlas_advanced_clusters data source results"
  type = object({
    name                                 = string
    project_id                           = string
    cluster_type                         = string
    mongo_db_major_version               = string
    backup_enabled                       = bool
    pit_enabled                          = bool
    termination_protection_enabled       = bool
    redact_client_log_data               = bool
    encryption_at_rest_provider          = string
    version_release_system               = string
    global_cluster_self_managed_sharding = bool
    replica_set_scaling_strategy         = string
    tags                                 = map(string)
    labels                               = map(string)

    advanced_configuration = object({
      change_stream_options_pre_and_post_images_expire_after_seconds = number
      custom_openssl_cipher_config_tls12                             = set(string)
      default_max_time_ms                                            = number
      default_write_concern                                          = string
      javascript_enabled                                             = bool
      minimum_enabled_tls_protocol                                   = string
      no_table_scan                                                  = bool
      oplog_min_retention_hours                                      = number
      oplog_size_mb                                                  = number
      sample_refresh_interval_bi_connector                           = number
      sample_size_bi_connector                                       = number
      tls_cipher_config_mode                                         = string
      transaction_lifetime_limit_seconds                             = number
    })

    bi_connector_config = object({
      enabled         = bool
      read_preference = string
    })

    replication_specs = list(object({
      zone_name    = string
      external_id  = string
      zone_id      = string
      container_id = map(string)

      region_configs = list(object({
        region_name           = string
        provider_name         = string
        priority              = number
        backing_provider_name = string

        electable_specs = object({
          instance_size   = string
          node_count      = number
          disk_size_gb    = number
          disk_iops       = number
          ebs_volume_type = string
        })

        read_only_specs = object({
          instance_size   = string
          node_count      = number
          disk_size_gb    = number
          disk_iops       = number
          ebs_volume_type = string
        })

        analytics_specs = object({
          instance_size   = string
          node_count      = number
          disk_size_gb    = number
          disk_iops       = number
          ebs_volume_type = string
        })

        auto_scaling = object({
          compute_enabled            = bool
          compute_max_instance_size  = string
          compute_min_instance_size  = string
          compute_scale_down_enabled = bool
          disk_gb_enabled            = bool
        })

        analytics_auto_scaling = object({
          compute_enabled            = bool
          compute_max_instance_size  = string
          compute_min_instance_size  = string
          compute_scale_down_enabled = bool
          disk_gb_enabled            = bool
        })
      }))
    }))
  })
}
