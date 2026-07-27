# Plan tests for modules/_autoscaling_instance_size (used by root electable auto-scaling).
# Cannot mock data.mongodbatlas_advanced_clusters.results end-to-end today:
# override_data fails on Plugin Framework nested_type lists (tuple vs object).

run "above_max_clamps_to_max" {
  command = plan
  module { source = "./modules/_autoscaling_instance_size" }

  variables {
    existing_instance_size     = "M80"
    compute_max_instance_size  = "M40"
    compute_min_instance_size  = "M10"
    compute_scale_down_enabled = true
  }

  assert {
    condition     = output.instance_size == "M40"
    error_message = "Expected M80 above max M40 to clamp to M40, got ${output.instance_size}"
  }
}

run "below_min_clamps_to_min_when_scale_down_enabled" {
  command = plan
  module { source = "./modules/_autoscaling_instance_size" }

  variables {
    existing_instance_size     = "M10"
    compute_max_instance_size  = "M40"
    compute_min_instance_size  = "M30"
    compute_scale_down_enabled = true
  }

  assert {
    condition     = output.instance_size == "M30"
    error_message = "Expected M10 below min M30 to clamp to M30, got ${output.instance_size}"
  }
}

run "below_min_keeps_existing_when_scale_down_disabled" {
  command = plan
  module { source = "./modules/_autoscaling_instance_size" }

  variables {
    existing_instance_size     = "M10"
    compute_max_instance_size  = "M40"
    compute_min_instance_size  = "M30"
    compute_scale_down_enabled = false
  }

  assert {
    condition     = output.instance_size == "M10"
    error_message = "Expected M10 below min to stay M10 when scale-down disabled, got ${output.instance_size}"
  }
}

run "in_range_keeps_existing" {
  command = plan
  module { source = "./modules/_autoscaling_instance_size" }

  variables {
    existing_instance_size     = "M30"
    compute_max_instance_size  = "M40"
    compute_min_instance_size  = "M10"
    compute_scale_down_enabled = true
  }

  assert {
    condition     = output.instance_size == "M30"
    error_message = "Expected in-range M30 to stay M30, got ${output.instance_size}"
  }
}

run "nvme_above_max_clamps_to_max" {
  command = plan
  module { source = "./modules/_autoscaling_instance_size" }

  variables {
    existing_instance_size     = "M80_NVME"
    compute_max_instance_size  = "M40_NVME"
    compute_min_instance_size  = "M10"
    compute_scale_down_enabled = true
  }

  assert {
    condition     = output.instance_size == "M40_NVME"
    error_message = "Expected M80_NVME above max to clamp to M40_NVME, got ${output.instance_size}"
  }
}

run "null_existing_uses_min" {
  command = plan
  module { source = "./modules/_autoscaling_instance_size" }

  variables {
    existing_instance_size     = null
    compute_max_instance_size  = "M40"
    compute_min_instance_size  = "M20"
    compute_scale_down_enabled = true
  }

  assert {
    condition     = output.instance_size == "M20"
    error_message = "Expected null existing (create path) to use min M20, got ${output.instance_size}"
  }
}

run "lexicographic_trap_m100_vs_m40" {
  command = plan
  module { source = "./modules/_autoscaling_instance_size" }

  variables {
    existing_instance_size     = "M100"
    compute_max_instance_size  = "M40"
    compute_min_instance_size  = "M10"
    compute_scale_down_enabled = true
  }

  assert {
    condition     = output.instance_size == "M40"
    error_message = "Numeric compare must treat M100 > M40 (string compare would not); got ${output.instance_size}"
  }
}
