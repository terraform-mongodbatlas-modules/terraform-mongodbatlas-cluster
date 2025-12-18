variable "mongodbatlas_database_user" {
  type = object({
    auth_database_name = string,
    project_id         = string,
    username           = string,
    aws_iam_type       = optional(string),
    description        = optional(string),
    labels = optional(set(object({
      key   = optional(string),
      value = optional(string)
    }))),
    ldap_auth_type = optional(string),
    oidc_auth_type = optional(string),
    password       = optional(string),
    roles = optional(set(object({
      collection_name = optional(string),
      database_name   = string,
      role_name       = string
    }))),
    scopes = optional(set(object({
      name = optional(string),
      type = optional(string)
    }))),
    x509_type = optional(string)
  })
}