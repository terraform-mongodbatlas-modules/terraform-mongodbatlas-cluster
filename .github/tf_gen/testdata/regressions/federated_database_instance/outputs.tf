output "hostnames" {
  value = mongodbatlas_federated_database_instance.this.hostnames
}

output "id" {
  value = mongodbatlas_federated_database_instance.this.id
}

output "state" {
  value = mongodbatlas_federated_database_instance.this.state
}

output "storage_databases_max_wildcard_collections" {
  value = mongodbatlas_federated_database_instance.this.storage_databases == null ? null : mongodbatlas_federated_database_instance.this.storage_databases[*].max_wildcard_collections
}

output "storage_databases_name" {
  value = mongodbatlas_federated_database_instance.this.storage_databases == null ? null : mongodbatlas_federated_database_instance.this.storage_databases[*].name
}

output "storage_stores_additional_storage_classes" {
  value = mongodbatlas_federated_database_instance.this.storage_stores == null ? null : mongodbatlas_federated_database_instance.this.storage_stores[*].additional_storage_classes
}

output "storage_stores_allow_insecure" {
  value = mongodbatlas_federated_database_instance.this.storage_stores == null ? null : mongodbatlas_federated_database_instance.this.storage_stores[*].allow_insecure
}

output "storage_stores_bucket" {
  value = mongodbatlas_federated_database_instance.this.storage_stores == null ? null : mongodbatlas_federated_database_instance.this.storage_stores[*].bucket
}

output "storage_stores_cluster_name" {
  value = mongodbatlas_federated_database_instance.this.storage_stores == null ? null : mongodbatlas_federated_database_instance.this.storage_stores[*].cluster_name
}

output "storage_stores_default_format" {
  value = mongodbatlas_federated_database_instance.this.storage_stores == null ? null : mongodbatlas_federated_database_instance.this.storage_stores[*].default_format
}