output "cloud_provider_access_setup" {
  value = {
    aws_config = mongodbatlas_cloud_provider_access_setup.this.aws_config
    created_date = mongodbatlas_cloud_provider_access_setup.this.created_date
    gcp_config = mongodbatlas_cloud_provider_access_setup.this.gcp_config
    id = mongodbatlas_cloud_provider_access_setup.this.id
    last_updated_date = mongodbatlas_cloud_provider_access_setup.this.last_updated_date
    role_id = mongodbatlas_cloud_provider_access_setup.this.role_id
  }
}