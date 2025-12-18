resource "mongodbatlas_cloud_provider_access_setup" "this" {
  delete_on_create_timeout = var.delete_on_create_timeout
  project_id               = var.project_id
  provider_name            = var.provider_name

  dynamic "azure_config" {
    for_each = var.azure_config == null ? [] : var.azure_config
    content {
      atlas_azure_app_id   = azure_config.value.atlas_azure_app_id
      service_principal_id = azure_config.value.service_principal_id
      tenant_id            = azure_config.value.tenant_id
    }
  }
}