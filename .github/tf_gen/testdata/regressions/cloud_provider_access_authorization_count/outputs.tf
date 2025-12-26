output "authorized_date" {
  value = length(mongodbatlas_cloud_provider_access_authorization.this) > 0 ? mongodbatlas_cloud_provider_access_authorization.this[0].authorized_date : null
}

output "feature_usages" {
  value = length(mongodbatlas_cloud_provider_access_authorization.this) > 0 ? mongodbatlas_cloud_provider_access_authorization.this[0].feature_usages : null
}

output "gcp" {
  value = length(mongodbatlas_cloud_provider_access_authorization.this) > 0 ? mongodbatlas_cloud_provider_access_authorization.this[0].gcp : null
}

output "id" {
  value = length(mongodbatlas_cloud_provider_access_authorization.this) > 0 ? mongodbatlas_cloud_provider_access_authorization.this[0].id : null
}