resource "mongodbatlas_advanced_cluster" "this" {
  accept_data_risks_and_force_replica_set_reconfig = var.mongodbatlas_advanced_cluster.accept_data_risks_and_force_replica_set_reconfig
  advanced_configuration                           = var.mongodbatlas_advanced_cluster.advanced_configuration
  backup_enabled                                   = var.mongodbatlas_advanced_cluster.backup_enabled
  bi_connector_config                              = var.mongodbatlas_advanced_cluster.bi_connector_config
  cluster_type                                     = var.mongodbatlas_advanced_cluster.cluster_type
  config_server_management_mode                    = var.mongodbatlas_advanced_cluster.config_server_management_mode
  delete_on_create_timeout                         = var.mongodbatlas_advanced_cluster.delete_on_create_timeout
  encryption_at_rest_provider                      = var.mongodbatlas_advanced_cluster.encryption_at_rest_provider
  global_cluster_self_managed_sharding             = var.mongodbatlas_advanced_cluster.global_cluster_self_managed_sharding
  labels                                           = var.mongodbatlas_advanced_cluster.labels
  mongo_db_major_version                           = var.mongodbatlas_advanced_cluster.mongo_db_major_version
  name                                             = var.mongodbatlas_advanced_cluster.name
  paused                                           = var.mongodbatlas_advanced_cluster.paused
  pinned_fcv                                       = var.mongodbatlas_advanced_cluster.pinned_fcv
  pit_enabled                                      = var.mongodbatlas_advanced_cluster.pit_enabled
  project_id                                       = var.mongodbatlas_advanced_cluster.project_id
  redact_client_log_data                           = var.mongodbatlas_advanced_cluster.redact_client_log_data
  replica_set_scaling_strategy                     = var.mongodbatlas_advanced_cluster.replica_set_scaling_strategy
  replication_specs                                = var.mongodbatlas_advanced_cluster.replication_specs
  retain_backups_enabled                           = var.mongodbatlas_advanced_cluster.retain_backups_enabled
  root_cert_type                                   = var.mongodbatlas_advanced_cluster.root_cert_type
  tags                                             = var.mongodbatlas_advanced_cluster.tags
  termination_protection_enabled                   = var.mongodbatlas_advanced_cluster.termination_protection_enabled
  timeouts                                         = var.mongodbatlas_advanced_cluster.timeouts
  use_effective_fields                             = var.mongodbatlas_advanced_cluster.use_effective_fields
  version_release_system                           = var.mongodbatlas_advanced_cluster.version_release_system
}