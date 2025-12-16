variable "vpc_id" {
  type = string
}

variable "auto_accept" {
  type     = bool
  nullable = true
  default  = null
}

variable "dns_options" {
  type     = object({ dns_record_ip_type = optional(string), private_dns_only_for_inbound_resolver_endpoint = optional(bool) })
  nullable = true
  default  = null
}

variable "ip_address_type" {
  type     = string
  nullable = true
  default  = null
}

variable "policy" {
  type     = string
  nullable = true
  default  = null
}

variable "private_dns_enabled" {
  type     = bool
  nullable = true
  default  = null
}

variable "resource_configuration_arn" {
  type     = string
  nullable = true
  default  = null
}

variable "route_table_ids" {
  type     = set(string)
  nullable = true
  default  = null
}

variable "security_group_ids" {
  type     = set(string)
  nullable = true
  default  = null
}

variable "service_name" {
  type     = string
  nullable = true
  default  = null
}

variable "service_network_arn" {
  type     = string
  nullable = true
  default  = null
}

variable "service_region" {
  type     = string
  nullable = true
  default  = null
}

variable "subnet_configuration" {
  type     = set(object({ ipv4 = optional(string), ipv6 = optional(string), subnet_id = optional(string) }))
  nullable = true
  default  = null
}

variable "subnet_ids" {
  type     = set(string)
  nullable = true
  default  = null
}

variable "tags" {
  type     = map(string)
  nullable = true
  default  = null
}

variable "tags_all" {
  type     = map(string)
  nullable = true
  default  = null
}

variable "timeouts" {
  type     = object({ create = optional(string), delete = optional(string), update = optional(string) })
  nullable = true
  default  = null
}

variable "vpc_endpoint_type" {
  type     = string
  nullable = true
  default  = null
}