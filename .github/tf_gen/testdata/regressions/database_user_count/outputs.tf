output "aws_iam_type" {
  value = mongodbatlas_database_user.this[0].aws_iam_type
}

output "id" {
  value = mongodbatlas_database_user.this[0].id
}

output "labels_key" {
  value = mongodbatlas_database_user.this[0].labels == null ? null : mongodbatlas_database_user.this[0].labels[*].key
}

output "labels_value" {
  value = mongodbatlas_database_user.this[0].labels == null ? null : mongodbatlas_database_user.this[0].labels[*].value
}

output "ldap_auth_type" {
  value = mongodbatlas_database_user.this[0].ldap_auth_type
}

output "oidc_auth_type" {
  value = mongodbatlas_database_user.this[0].oidc_auth_type
}

output "x509_type" {
  value = mongodbatlas_database_user.this[0].x509_type
}