resource "mongodbatlas_cloud_provider_access_authorization" "this" {
  project_id = var.mongodbatlas_cloud_provider_access_authorization.project_id
  role_id    = var.mongodbatlas_cloud_provider_access_authorization.role_id

  dynamic "aws" {
    for_each = var.mongodbatlas_cloud_provider_access_authorization.aws == null ? [] : [var.mongodbatlas_cloud_provider_access_authorization.aws]
    content {
      iam_assumed_role_arn = aws.value.iam_assumed_role_arn
    }
  }

  dynamic "azure" {
    for_each = var.mongodbatlas_cloud_provider_access_authorization.azure == null ? [] : [var.mongodbatlas_cloud_provider_access_authorization.azure]
    content {
      atlas_azure_app_id   = azure.value.atlas_azure_app_id
      service_principal_id = azure.value.service_principal_id
      tenant_id            = azure.value.tenant_id
    }
  }
}