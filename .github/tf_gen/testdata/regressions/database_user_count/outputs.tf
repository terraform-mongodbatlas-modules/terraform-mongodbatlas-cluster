output "aws_iam_type" {
  value = length(mongodbatlas_database_user.this) > 0 ? mongodbatlas_database_user.this[0].aws_iam_type : null
}

output "labels_key" {
  value = length(mongodbatlas_database_user.this) > 0 && mongodbatlas_database_user.this[0].labels != null ? mongodbatlas_database_user.this[0].labels[*].key : null
}

output "labels_value" {
  value = length(mongodbatlas_database_user.this) > 0 && mongodbatlas_database_user.this[0].labels != null ? mongodbatlas_database_user.this[0].labels[*].value : null
}

output "ldap_auth_type" {
  value = length(mongodbatlas_database_user.this) > 0 ? mongodbatlas_database_user.this[0].ldap_auth_type : null
}

output "oidc_auth_type" {
  value = length(mongodbatlas_database_user.this) > 0 ? mongodbatlas_database_user.this[0].oidc_auth_type : null
}

output "x509_type" {
  value = length(mongodbatlas_database_user.this) > 0 ? mongodbatlas_database_user.this[0].x509_type : null
}