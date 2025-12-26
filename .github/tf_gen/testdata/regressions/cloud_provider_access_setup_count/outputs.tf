output "aws_config" {
  value = length(mongodbatlas_cloud_provider_access_setup.this) > 0 ? mongodbatlas_cloud_provider_access_setup.this[0].aws_config : null
}

output "created_date" {
  value = length(mongodbatlas_cloud_provider_access_setup.this) > 0 ? mongodbatlas_cloud_provider_access_setup.this[0].created_date : null
}

output "gcp_config" {
  value = length(mongodbatlas_cloud_provider_access_setup.this) > 0 ? mongodbatlas_cloud_provider_access_setup.this[0].gcp_config : null
}

output "id" {
  value = length(mongodbatlas_cloud_provider_access_setup.this) > 0 ? mongodbatlas_cloud_provider_access_setup.this[0].id : null
}

output "last_updated_date" {
  value = length(mongodbatlas_cloud_provider_access_setup.this) > 0 ? mongodbatlas_cloud_provider_access_setup.this[0].last_updated_date : null
}

output "role_id" {
  value = length(mongodbatlas_cloud_provider_access_setup.this) > 0 ? mongodbatlas_cloud_provider_access_setup.this[0].role_id : null
}