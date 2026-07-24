variable "existing_instance_size" {
  type        = string
  default     = null
  description = "Current instance size from an existing cluster, or null on create."
}

variable "compute_max_instance_size" {
  type        = string
  description = "Auto-scaling compute max instance size."
}

variable "compute_min_instance_size" {
  type        = string
  description = "Auto-scaling compute min instance size."
}

variable "compute_scale_down_enabled" {
  type        = bool
  description = "Whether auto-scaling may scale below the current size down to compute_min_instance_size."
}

# Numeric tier compare (M10 / M40_NVME → 10 / 40). Terraform min()/max() reject strings.
locals {
  instance_size = var.existing_instance_size == null ? var.compute_min_instance_size : (
    tonumber(regex("[0-9]+", var.existing_instance_size)) > tonumber(regex("[0-9]+", var.compute_max_instance_size))
    ? var.compute_max_instance_size
    : (
      var.compute_scale_down_enabled
      && tonumber(regex("[0-9]+", var.existing_instance_size)) < tonumber(regex("[0-9]+", var.compute_min_instance_size))
    )
    ? var.compute_min_instance_size
    : var.existing_instance_size
  )
}

output "instance_size" {
  value       = local.instance_size
  description = "Instance size clamped into auto-scaling bounds."
}
