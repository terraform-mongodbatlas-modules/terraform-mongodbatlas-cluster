output "advanced_cluster" {
  value = {
    advanced_configuration = mongodbatlas_advanced_cluster.this.advanced_configuration
    backup_enabled = mongodbatlas_advanced_cluster.this.backup_enabled
    bi_connector_config = mongodbatlas_advanced_cluster.this.bi_connector_config
    cluster_id = mongodbatlas_advanced_cluster.this.cluster_id
    config_server_management_mode = mongodbatlas_advanced_cluster.this.config_server_management_mode
    config_server_type = mongodbatlas_advanced_cluster.this.config_server_type
    connection_strings = mongodbatlas_advanced_cluster.this.connection_strings
    create_date = mongodbatlas_advanced_cluster.this.create_date
    delete_on_create_timeout = mongodbatlas_advanced_cluster.this.delete_on_create_timeout
    encryption_at_rest_provider = mongodbatlas_advanced_cluster.this.encryption_at_rest_provider
    global_cluster_self_managed_sharding = mongodbatlas_advanced_cluster.this.global_cluster_self_managed_sharding
    mongo_db_major_version = mongodbatlas_advanced_cluster.this.mongo_db_major_version
    mongo_db_version = mongodbatlas_advanced_cluster.this.mongo_db_version
    paused = mongodbatlas_advanced_cluster.this.paused
    pit_enabled = mongodbatlas_advanced_cluster.this.pit_enabled
    redact_client_log_data = mongodbatlas_advanced_cluster.this.redact_client_log_data
    replica_set_scaling_strategy = mongodbatlas_advanced_cluster.this.replica_set_scaling_strategy
    root_cert_type = mongodbatlas_advanced_cluster.this.root_cert_type
    state_name = mongodbatlas_advanced_cluster.this.state_name
    termination_protection_enabled = mongodbatlas_advanced_cluster.this.termination_protection_enabled
    version_release_system = mongodbatlas_advanced_cluster.this.version_release_system
  }
}