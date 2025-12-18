resource "mongodbatlas_database_user" "this" {
  auth_database_name = var.auth_database_name
  aws_iam_type       = var.aws_iam_type
  description        = var.description
  ldap_auth_type     = var.ldap_auth_type
  oidc_auth_type     = var.oidc_auth_type
  password           = var.password
  project_id         = var.project_id
  username           = var.username
  x509_type          = var.x509_type

  dynamic "labels" {
    for_each = var.labels == null ? [] : var.labels
    content {
      key   = labels.value.key
      value = labels.value.value
    }
  }

  dynamic "roles" {
    for_each = var.roles == null ? [] : var.roles
    content {
      collection_name = roles.value.collection_name
      database_name   = roles.value.database_name
      role_name       = roles.value.role_name
    }
  }

  dynamic "scopes" {
    for_each = var.scopes == null ? [] : var.scopes
    content {
      name = scopes.value.name
      type = scopes.value.type
    }
  }
}