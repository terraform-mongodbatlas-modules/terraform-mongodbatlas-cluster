module "cluster" {
  source = "../.."

  name         = "cluster-with-backup"
  project_id   = var.project_id
  cluster_type = "SHARDED"
  regions = [
    {
      name          = "US_EAST_1"
      node_count    = 3
      provider_name = "AWS"
      shard_name    = "s1"
    },
    {
      # Auto-derived copy target (see backup_copy_region below).
      name          = "US_WEST_2"
      node_count    = 2
      provider_name = "AWS"
      shard_name    = "s1"
    }
  ]

  # backup_enabled defaults to true.
  backup_mode = "SCHEDULED" # module-managed policies. Other options: ON_DEMAND (manual snapshots only), UNMANAGED (customer-managed schedule).

  # Keep daily snapshots for 30 days instead of the 7-day default, and keep 14 days of
  # those on the cross-region copy (a copy_retention_value cannot exceed the source retention).
  # Atlas requires each less frequent policy item to retain at least as long as the more frequent
  # one, so weekly is raised above the default 4 weeks (28 days) to cover the 30-day daily retention.
  backup_retention = {
    daily  = { retention_value = 30, copy_retention_value = 14 }
    weekly = { retention_value = 5 }
  }

  # Omitting `region` auto-derives the secondary from `regions` above (US_WEST_2). To pin an explicit
  # target instead: backup_copy_region = { region = "EU_WEST_1" }, or name several with
  # backup_copy_region = { regions = ["US_WEST_2", "EU_WEST_1"] }.
  backup_copy_region = {
    # Apply retention changes to copies Atlas already took, and delete a copy when its policy item is removed.
    update_copy_snapshots = true
    delete_copy_snapshots = true
  }

  # Set to true when a Backup Compliance Policy is enabled on the project.
  backup_schedule_skip_destroy = true

  tags = var.tags
}

output "cluster" {
  value = module.cluster
}
