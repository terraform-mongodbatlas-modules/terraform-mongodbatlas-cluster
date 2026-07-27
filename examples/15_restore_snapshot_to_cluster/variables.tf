variable "project_id" {
  description = <<-EOT
Unique 24-hexadecimal digit string that identifies your project. You can find it by listing your projects in the Admin API or selecting a project in the Atlas UI and copying the path in the URL.

**NOTE**: Groups and projects are synonymous terms. Your group id is the same as your project id. For existing groups, your group/project id remains the same. The resource and corresponding endpoints use the term groups.
EOT

  type = string
}


variable "tags" {
  description = <<-EOT
Map that contains key-value pairs for tagging and categorizing the cluster. Each tag is between 1 to 255 characters in length.
We recommend setting the following tags:
- `department`
- `team_name`
- `application_name`
- `environment`
- `version`
- `email_contact`
- `criticality`

These values can be used for:
- Billing.
- Data classification.
- Regional compliance requirements for audit and governance purposes.
EOT
  type        = map(string)
  nullable    = true
  default     = null
}

variable "restore_point_in_time_utc_seconds" {
  description = <<-EOT
  Unix timestamp (seconds) to restore to, using the point-in-time delivery type instead of an
  automated (snapshot-as-is) restore. Leave unset for an automated restore.
  EOT
  type        = number
  nullable    = true
  default     = null
}
