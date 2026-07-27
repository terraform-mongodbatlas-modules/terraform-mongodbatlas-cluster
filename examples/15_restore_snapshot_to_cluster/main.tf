module "source" {
  source = "../.."

  name         = "restore-source"
  project_id   = var.project_id
  cluster_type = "REPLICASET"
  regions = [
    {
      name       = "US_EAST_1"
      node_count = 3
    }
  ]
  provider_name = "AWS"

  # ON_DEMAND keeps this example focused on the manual snapshot + restore job below, instead of
  # also provisioning the default recurring schedule (see docs/backup_guide.md).
  backup_mode = "ON_DEMAND"

  tags = var.tags
}

module "target" {
  source = "../.."

  name         = "restore-target"
  project_id   = var.project_id
  cluster_type = "REPLICASET"
  regions = [
    {
      name       = "US_EAST_1"
      node_count = 3
    }
  ]
  provider_name = "AWS"

  backup_mode = "ON_DEMAND"

  tags = var.tags
}

# On-demand snapshot; use backup_mode/backup_retention instead for a recurring schedule (see docs/backup_guide.md).
resource "mongodbatlas_cloud_backup_snapshot" "this" {
  project_id        = var.project_id
  cluster_name      = module.source.cluster_name
  description       = "On-demand snapshot for the restore-job example"
  retention_in_days = 2
}

# Restore jobs are one-off actions, not module-managed. Restoring wipes all existing data on the target cluster.
resource "mongodbatlas_cloud_backup_snapshot_restore_job" "this" {
  project_id   = var.project_id
  cluster_name = module.source.cluster_name
  snapshot_id  = mongodbatlas_cloud_backup_snapshot.this.snapshot_id

  delivery_type_config {
    # Set var.restore_point_in_time_utc_seconds to restore to a specific instant (point-in-time)
    # instead of the snapshot as-is (automated). See docs/backup_guide.md for the third delivery
    # type, download, which isn't modeled here.
    automated                 = var.restore_point_in_time_utc_seconds == null
    point_in_time             = var.restore_point_in_time_utc_seconds != null
    target_cluster_name       = module.target.cluster_name
    target_project_id         = var.project_id
    point_in_time_utc_seconds = var.restore_point_in_time_utc_seconds
  }
}

output "source_cluster" {
  value = module.source
}

output "target_cluster" {
  value = module.target
}
