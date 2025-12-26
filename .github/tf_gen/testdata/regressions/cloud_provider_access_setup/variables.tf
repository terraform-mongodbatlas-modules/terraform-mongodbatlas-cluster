variable "project_id" {
  type = string
}

variable "provider_name" {
  type = string
}

variable "azure_config" {
  type = list(object({
    atlas_azure_app_id   = string,
    service_principal_id = string,
    tenant_id            = string
  }))
  nullable = true
  default  = null
}

variable "delete_on_create_timeout" {
  type        = bool
  description = "Indicates whether to delete the resource being created if a timeout is reached when waiting for completion. When set to `true` and timeout occurs, it triggers the deletion and returns immediately without waiting for deletion to complete. When set to `false`, the timeout will not trigger resource deletion. If you suspect a transient error when the value is `true`, wait before retrying to allow resource deletion to finish. Default is `true`."
  nullable    = true
  default     = null
}

variable "timeouts" {
  type = object({
    create = optional(string)
  })
  nullable = true
  default  = null
}