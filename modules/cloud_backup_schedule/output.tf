output "cluster_id" {
  value = mongodbatlas_cloud_backup_schedule.this.cluster_id
}

output "id_policy" {
  value = mongodbatlas_cloud_backup_schedule.this.id_policy
}

output "next_snapshot" {
  value = mongodbatlas_cloud_backup_schedule.this.next_snapshot
}
