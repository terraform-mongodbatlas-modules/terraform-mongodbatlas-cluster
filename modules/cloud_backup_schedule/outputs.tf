output "schedule" {
  description = "Internal-only: exposes the managed schedule resource so terraform test can assert on its attributes. This submodule is not invoked directly by consumers, and the root cluster module does not re-export this output."
  value       = mongodbatlas_cloud_backup_schedule.this
}
