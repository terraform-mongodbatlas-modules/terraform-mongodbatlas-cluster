variable "auth_database_name" {
  type = string
}

variable "project_id" {
  type = string
}

variable "username" {
  type = string
}

variable "aws_iam_type" {
  type     = string
  nullable = true
  default  = null
}

variable "description" {
  type     = string
  nullable = true
  default  = null
}

variable "labels" {
  type     = set(object({ key = optional(string), value = optional(string) }))
  nullable = true
  default  = null
}

variable "ldap_auth_type" {
  type     = string
  nullable = true
  default  = null
}

variable "oidc_auth_type" {
  type     = string
  nullable = true
  default  = null
}

variable "password" {
  type      = string
  nullable  = true
  default   = null
  sensitive = true
}

variable "roles" {
  type     = set(object({ collection_name = optional(string), database_name = string, role_name = string }))
  nullable = true
  default  = null
}

variable "scopes" {
  type     = set(object({ name = optional(string), type = optional(string) }))
  nullable = true
  default  = null
}

variable "x509_type" {
  type     = string
  nullable = true
  default  = null
}