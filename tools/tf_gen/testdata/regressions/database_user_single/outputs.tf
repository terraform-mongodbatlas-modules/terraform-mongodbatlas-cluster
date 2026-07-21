output "database_user" {
  value = {
    aws_iam_type = mongodbatlas_database_user.this.aws_iam_type
    labels = mongodbatlas_database_user.this.labels
    ldap_auth_type = mongodbatlas_database_user.this.ldap_auth_type
    oidc_auth_type = mongodbatlas_database_user.this.oidc_auth_type
    x509_type = mongodbatlas_database_user.this.x509_type
  }
}