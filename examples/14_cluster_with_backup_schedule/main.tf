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
      shard_number  = 1
    },
    {
      # Auto-derived copy target (see backup_copy_region below).
      name          = "US_WEST_2"
      node_count    = 2
      provider_name = "AWS"
      shard_number  = 1
    }
  ]

  # backup_enabled defaults to true.
  backup_mode = "SCHEDULED" # module-managed policies. Other options: ON_DEMAND (manual snapshots only), UNMANAGED (customer-managed schedule).

  # Keep daily snapshots for 30 days instead of the 7-day default.
  backup_retention = {
    daily = { retention_value = 30 }
  }

  # Omitting `region` auto-derives the secondary from `regions` above (US_WEST_2). To pin an explicit
  # target instead: backup_copy_region = { region = "EU_WEST_1" }
  backup_copy_region = {}

  # Set to true when a Backup Compliance Policy is enabled on the project.
  backup_schedule_skip_destroy = true

  tags = var.tags
}

output "cluster" {
  value = module.cluster
}
