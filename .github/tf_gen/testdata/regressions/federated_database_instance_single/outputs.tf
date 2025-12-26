output "federated_database_instance" {
  value = {
    hostnames = mongodbatlas_federated_database_instance.this.hostnames
    state = mongodbatlas_federated_database_instance.this.state
    storage_databases = mongodbatlas_federated_database_instance.this.storage_databases
    storage_stores = mongodbatlas_federated_database_instance.this.storage_stores
  }
}