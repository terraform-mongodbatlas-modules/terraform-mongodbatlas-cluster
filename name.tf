locals {
  # POST: HTTP 400 Bad Request (Error code: "CLUSTER_NAME_PREFIX_INVALID") Detail: Cluster name "more-than-thirty-three-check-long-name-very-long-even--chars" is invalid.
  # Atlas truncates cluster names to 23 characters which results in an invalid hostname due to a trailing "-" in the generated cluster name prefix "more-than-thirty-three-".
  max_length    = 23
  generate_name = var.name == ""

  raw_name   = local.generate_name ? random_pet.generated_name[0].id : var.name
  short_name = local.generate_name ? substr(local.raw_name, 0, local.max_length) : var.name
  final_name = local.generate_name ? trim(local.short_name, "-") : var.name
}

resource "random_pet" "generated_name" {
  count = local.generate_name ? 1 : 0

  prefix = trim(var.name_prefix, "-")
  length = 2
  keepers = {
    prefix = var.name_prefix
  }
}
