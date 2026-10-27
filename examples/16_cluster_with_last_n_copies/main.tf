module "cluster" {
  source = "../.."

  name         = "cluster-with-last-n-copies"
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
      # Copy targets (see backup_copy_region below).
      name          = "US_WEST_2"
      node_count    = 2
      provider_name = "AWS"
      shard_name    = "s1"
    },
    {
      # Copy targets (see backup_copy_region below).
      name          = "EU_WEST_1"
      node_count    = 2
      provider_name = "AWS"
      shard_name    = "s1"
    }
  ]

  # backup_enabled defaults to true.
  backup_mode = "SCHEDULED" # module-managed policies. Other options: ON_DEMAND (manual snapshots only), UNMANAGED (customer-managed schedule).

  # Keep daily snapshots for 30 days instead of the 7-day default. Atlas requires each less frequent
  # policy item to retain at least as long as the more frequent one, so weekly is raised above the
  # default 4 weeks (28 days) to cover the 30-day daily retention.
  backup_retention = {
    daily  = { retention_value = 30 }
    weekly = { retention_value = 5 }
  }

  # Copy to the two highest-priority secondary regions (US_WEST_2 and EU_WEST_1) and keep a
  # rolling window of the last 5 copies in each. last_number_of_snapshots replaces the derived
  # copy_policy_items, so no per-frequency copy retention is sent for these targets.
  backup_copy_region = {
    region_count             = 2
    last_number_of_snapshots = 5
  }

  # Set to true when a Backup Compliance Policy is enabled on the project: Terraform removes the schedule
  # from state on destroy without deleting it in Atlas, so Atlas keeps creating snapshots.
  backup_schedule_skip_destroy = true

  tags = var.tags
}

output "cluster" {
  value = module.cluster
}
