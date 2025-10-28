# Outputs from the import module
# The generated .tf file is written to the output_directory

output "generated_filename" {
  description = "Name of the generated .tf file"
  value       = "${module.cluster_import.name}.tf"
}

output "summary" {
  description = "Summary of the imported cluster"
  value       = module.cluster_import.summary
}
