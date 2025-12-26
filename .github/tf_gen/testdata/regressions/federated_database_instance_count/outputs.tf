output "hostnames" {
  value = length(mongodbatlas_federated_database_instance.this) > 0 ? mongodbatlas_federated_database_instance.this[0].hostnames : null
}

output "id" {
  value = length(mongodbatlas_federated_database_instance.this) > 0 ? mongodbatlas_federated_database_instance.this[0].id : null
}

output "state" {
  value = length(mongodbatlas_federated_database_instance.this) > 0 ? mongodbatlas_federated_database_instance.this[0].state : null
}

output "storage_databases_max_wildcard_collections" {
  value = length(mongodbatlas_federated_database_instance.this) > 0 && mongodbatlas_federated_database_instance.this[0].storage_databases != null ? mongodbatlas_federated_database_instance.this[0].storage_databases[*].max_wildcard_collections : null
}

output "storage_databases_name" {
  value = length(mongodbatlas_federated_database_instance.this) > 0 && mongodbatlas_federated_database_instance.this[0].storage_databases != null ? mongodbatlas_federated_database_instance.this[0].storage_databases[*].name : null
}

output "storage_stores_additional_storage_classes" {
  value = length(mongodbatlas_federated_database_instance.this) > 0 && mongodbatlas_federated_database_instance.this[0].storage_stores != null ? mongodbatlas_federated_database_instance.this[0].storage_stores[*].additional_storage_classes : null
}

output "storage_stores_allow_insecure" {
  value = length(mongodbatlas_federated_database_instance.this) > 0 && mongodbatlas_federated_database_instance.this[0].storage_stores != null ? mongodbatlas_federated_database_instance.this[0].storage_stores[*].allow_insecure : null
}

output "storage_stores_bucket" {
  value = length(mongodbatlas_federated_database_instance.this) > 0 && mongodbatlas_federated_database_instance.this[0].storage_stores != null ? mongodbatlas_federated_database_instance.this[0].storage_stores[*].bucket : null
}

output "storage_stores_cluster_name" {
  value = length(mongodbatlas_federated_database_instance.this) > 0 && mongodbatlas_federated_database_instance.this[0].storage_stores != null ? mongodbatlas_federated_database_instance.this[0].storage_stores[*].cluster_name : null
}

output "storage_stores_default_format" {
  value = length(mongodbatlas_federated_database_instance.this) > 0 && mongodbatlas_federated_database_instance.this[0].storage_stores != null ? mongodbatlas_federated_database_instance.this[0].storage_stores[*].default_format : null
}