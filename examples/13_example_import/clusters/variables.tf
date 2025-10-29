variable "project_id" {
  description = <<-EOT
Unique 24-hexadecimal digit string that identifies your project, for example `664619d870c247237f4b86a6`. It is found listing projects in the Admin API or selecting a project in the UI and copying the path in the URL.

**NOTE**: Groups and projects are synonymous terms. Your group id is the same as your project id. For existing groups, your group/project id remains the same. The resource and corresponding endpoints use the term groups.
EOT

  type = string
}
