output "aws_iam_type" {
  value = mongodbatlas_database_user.this.aws_iam_type
}

output "labels_key" {
  value = mongodbatlas_database_user.this.labels == null ? null : mongodbatlas_database_user.this.labels[*].key
}

output "labels_value" {
  value = mongodbatlas_database_user.this.labels == null ? null : mongodbatlas_database_user.this.labels[*].value
}

output "ldap_auth_type" {
  value = mongodbatlas_database_user.this.ldap_auth_type
}

output "oidc_auth_type" {
  value = mongodbatlas_database_user.this.oidc_auth_type
}

output "x509_type" {
  value = mongodbatlas_database_user.this.x509_type
}