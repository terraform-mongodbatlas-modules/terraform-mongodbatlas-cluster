output "schedule" {
  description = "Internal: the managed cloud_backup_schedule resource. Not re-exported by the root cluster module (see Decision 13) -- exists here only so tests can introspect the resource."
  value       = mongodbatlas_cloud_backup_schedule.this
}
