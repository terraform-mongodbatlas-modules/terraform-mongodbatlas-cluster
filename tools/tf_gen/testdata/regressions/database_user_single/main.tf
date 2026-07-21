resource "mongodbatlas_database_user" "this" {
  auth_database_name = var.mongodbatlas_database_user.auth_database_name
  aws_iam_type       = var.mongodbatlas_database_user.aws_iam_type
  description        = var.mongodbatlas_database_user.description
  ldap_auth_type     = var.mongodbatlas_database_user.ldap_auth_type
  oidc_auth_type     = var.mongodbatlas_database_user.oidc_auth_type
  password           = var.mongodbatlas_database_user.password
  project_id         = var.mongodbatlas_database_user.project_id
  username           = var.mongodbatlas_database_user.username
  x509_type          = var.mongodbatlas_database_user.x509_type

  dynamic "labels" {
    for_each = var.mongodbatlas_database_user.labels == null ? [] : var.mongodbatlas_database_user.labels
    content {
      key   = labels.value.key
      value = labels.value.value
    }
  }

  dynamic "roles" {
    for_each = var.mongodbatlas_database_user.roles == null ? [] : var.mongodbatlas_database_user.roles
    content {
      collection_name = roles.value.collection_name
      database_name   = roles.value.database_name
      role_name       = roles.value.role_name
    }
  }

  dynamic "scopes" {
    for_each = var.mongodbatlas_database_user.scopes == null ? [] : var.mongodbatlas_database_user.scopes
    content {
      name = scopes.value.name
      type = scopes.value.type
    }
  }
}