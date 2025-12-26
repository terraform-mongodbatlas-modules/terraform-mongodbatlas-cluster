variable "mongodbatlas_cloud_provider_access_authorization" {
  type = object({
    project_id = string,
    role_id    = string,
    aws = optional(object({
      iam_assumed_role_arn = string
    })),
    azure = optional(object({
      atlas_azure_app_id   = string,
      service_principal_id = string,
      tenant_id            = string
    }))
  })
}