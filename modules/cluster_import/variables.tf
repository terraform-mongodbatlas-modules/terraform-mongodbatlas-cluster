variable "cluster_name" {
  description = "Name of the cluster to import"
  type        = string
}

variable "project_id" {
  description = "MongoDB Atlas Project ID"
  type        = string
}

variable "output_directory" {
  description = "Directory where the generated .tf file will be written"
  type        = string
}

variable "filename" {
  description = "Name of the generated .tf file (without .tf extension). Defaults to cluster name if not specified."
  type        = string
  default     = null
}
