output "cloud_provider_access_authorization" {
  value = {
    authorized_date = mongodbatlas_cloud_provider_access_authorization.this.authorized_date
    feature_usages = mongodbatlas_cloud_provider_access_authorization.this.feature_usages
    gcp = mongodbatlas_cloud_provider_access_authorization.this.gcp
  }
}