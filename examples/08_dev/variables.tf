variable "project_id" {
  description = <<-EOT
Unique 24-hexadecimal digit string that identifies your project. Use the [/groups](#tag/Projects/operation/listProjects) endpoint to retrieve all projects to which the authenticated user has access.

**NOTE**: Groups and projects are synonymous terms. Your group id is the same as your project id. For existing groups, your group/project id remains the same. The resource and corresponding endpoints use the term groups.
EOT

  type = string
}

variable "cluster_name" {
  description = "The name of the MongoDB Atlas cluster."
  type        = string
  default     = "dev-cluster"
}

variable "provider_name" {
  description = "Cloud provider for the MongoDB Atlas cluster."
  type        = string
  default     = "AWS"
}

variable "region_name" {
  description = "Region where the MongoDB Atlas cluster will be deployed."
  type        = string
  default     = "US_EAST_1"
}

variable "instance_size" {
  description = "Fixed instance size for dev (use dedicated M10 to keep features consistent)."
  type        = string
  default     = "M10"
}

variable "tags" {
  description = "Map that contains key-value pairs between 1 to 255 characters in length for tagging and categorizing the cluster."
  type        = map(string)
  default     = {
    department  = "engineering"
    team        = "platform"
    application = "atlas-dev"
    environment = "dev"
    version     = "v1"
    email       = "devnull@example.com"
    criticality = "low"
  }
}
