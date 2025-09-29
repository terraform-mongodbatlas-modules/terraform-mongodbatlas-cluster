module "cluster" {
  source = "../.."

  auto_scaling = {
    compute_enabled = false
  }

  name       = "dev"
  project_id = var.project_id
  regions = [
    {
      name          = "US_EAST_1"
      node_count    = 3
      instance_size = "M10"
    }
  ]
  provider_name = "AWS"
}

output "cluster" {
  value = module.cluster
}
