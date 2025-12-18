variable "project_id" {
  type = string
}

variable "role_id" {
  type = string
}

variable "aws" {
  type = object({
    iam_assumed_role_arn = string
  })
  nullable = true
  default  = null
}

variable "azure" {
  type = object({
    atlas_azure_app_id   = string,
    service_principal_id = string,
    tenant_id            = string
  })
  nullable = true
  default  = null
}