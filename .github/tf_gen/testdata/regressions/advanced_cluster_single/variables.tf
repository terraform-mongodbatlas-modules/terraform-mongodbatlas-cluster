variable "mongodbatlas_advanced_cluster" {
  type = object({
    cluster_type = string,
    name         = string,
    project_id   = string,
    replication_specs = list(object({
      region_configs = list(object({
        analytics_auto_scaling = optional(object({
          compute_enabled            = optional(bool),
          compute_max_instance_size  = optional(string),
          compute_min_instance_size  = optional(string),
          compute_scale_down_enabled = optional(bool),
          disk_gb_enabled            = optional(bool)
        })),
        analytics_specs = optional(object({
          disk_iops       = optional(number),
          disk_size_gb    = optional(number),
          ebs_volume_type = optional(string),
          instance_size   = optional(string),
          node_count      = optional(number)
        })),
        auto_scaling = optional(object({
          compute_enabled            = optional(bool),
          compute_max_instance_size  = optional(string),
          compute_min_instance_size  = optional(string),
          compute_scale_down_enabled = optional(bool),
          disk_gb_enabled            = optional(bool)
        })),
        backing_provider_name = optional(string),
        electable_specs = optional(object({
          disk_iops       = optional(number),
          disk_size_gb    = optional(number),
          ebs_volume_type = optional(string),
          instance_size   = optional(string),
          node_count      = optional(number)
        })),
        priority      = number,
        provider_name = string,
        read_only_specs = optional(object({
          disk_iops       = optional(number),
          disk_size_gb    = optional(number),
          ebs_volume_type = optional(string),
          instance_size   = optional(string),
          node_count      = optional(number)
        })),
        region_name = string
      })),
      zone_name = optional(string)
    })),
    accept_data_risks_and_force_replica_set_reconfig = optional(string),
    advanced_configuration = optional(object({
      change_stream_options_pre_and_post_images_expire_after_seconds = optional(number),
      custom_openssl_cipher_config_tls12                             = optional(set(string)),
      custom_openssl_cipher_config_tls13                             = optional(set(string)),
      default_max_time_ms                                            = optional(number),
      default_write_concern                                          = optional(string),
      javascript_enabled                                             = optional(bool),
      minimum_enabled_tls_protocol                                   = optional(string),
      no_table_scan                                                  = optional(bool),
      oplog_min_retention_hours                                      = optional(number),
      oplog_size_mb                                                  = optional(number),
      sample_refresh_interval_bi_connector                           = optional(number),
      sample_size_bi_connector                                       = optional(number),
      tls_cipher_config_mode                                         = optional(string),
      transaction_lifetime_limit_seconds                             = optional(number)
    })),
    backup_enabled = optional(bool),
    bi_connector_config = optional(object({
      enabled         = optional(bool),
      read_preference = optional(string)
    })),
    config_server_management_mode        = optional(string),
    delete_on_create_timeout             = optional(bool),
    encryption_at_rest_provider          = optional(string),
    global_cluster_self_managed_sharding = optional(bool),
    labels                               = optional(map(string)),
    mongo_db_major_version               = optional(string),
    paused                               = optional(bool),
    pinned_fcv = optional(object({
      expiration_date = string
    })),
    pit_enabled                    = optional(bool),
    redact_client_log_data         = optional(bool),
    replica_set_scaling_strategy   = optional(string),
    retain_backups_enabled         = optional(bool),
    root_cert_type                 = optional(string),
    tags                           = optional(map(string)),
    termination_protection_enabled = optional(bool),
    timeouts = optional(object({
      create = optional(string),
      delete = optional(string),
      update = optional(string)
    })),
    use_effective_fields   = optional(bool),
    version_release_system = optional(string)
  })
}