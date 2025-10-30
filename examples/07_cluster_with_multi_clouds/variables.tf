variable "project_id" {
  description = <<-EOT
Unique 24-hexadecimal digit string that identifies your project, for example `664619d870c247237f4b86a6`. It is found listing projects in the Admin API or selecting a project in the UI and copying the path in the URL.

**NOTE**: Groups and projects are synonymous terms. Your group id is the same as your project id. For existing groups, your group/project id remains the same. The resource and corresponding endpoints use the term groups.
EOT

  type = string
}

variable "tags" {
  description = <<-EOT
Map that contains key-value pairs between 1 to 255 characters in length for tagging and categorizing the cluster.
We recommend setting:
Department, team name, application name, environment, version, email contact, criticality. 
These values can be used for:
- Billing.
- Data classification.
- Regional compliance requirements for audit and governance purposes.
EOT
  type        = map(string)
  default     = {}
}
