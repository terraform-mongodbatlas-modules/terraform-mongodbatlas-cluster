

resource "mongodbatlas_search_deployment" "this" {
  cluster_name             = var.cluster_name
  delete_on_create_timeout = var.delete_on_create_timeout
  project_id               = var.project_id
  skip_wait_on_update      = var.skip_wait_on_update
  specs                    = var.specs
  timeouts                 = var.timeouts
}
