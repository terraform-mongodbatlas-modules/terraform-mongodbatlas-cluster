module "cluster" {
  source = "../.."

  name       = var.cluster_name
  project_id = var.project_id

  # Dev-friendly: smallest dedicated tier, single region replicaset
  regions = [
    {
      name          = var.region_name
      node_count    = 3
      provider_name = var.provider_name
      instance_size = var.instance_size
    }
  ]

  # Keep costs down in dev
  backup_enabled                 = false
  retain_backups_enabled         = false
  termination_protection_enabled = true
  redact_client_log_data         = true

  # Prefer fixed instance size in dev to avoid scale surprises
  auto_scaling = {
    compute_enabled            = false
    disk_gb_enabled            = false
    compute_scale_down_enabled = false
  }

  # Sensible security/ops defaults
  advanced_configuration = {
    minimum_enabled_tls_protocol = "TLS1_2"
    default_write_concern        = "majority"
    javascript_enabled           = false
  }

  tags          = var.tags
}

output "cluster" {
  value = module.cluster
}
