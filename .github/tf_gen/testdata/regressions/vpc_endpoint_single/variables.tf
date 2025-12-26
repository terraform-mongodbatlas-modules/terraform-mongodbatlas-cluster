variable "aws_vpc_endpoint" {
  type = object({
    vpc_id      = string,
    auto_accept = optional(bool),
    dns_options = optional(object({
      dns_record_ip_type                             = optional(string),
      private_dns_only_for_inbound_resolver_endpoint = optional(bool)
    })),
    ip_address_type            = optional(string),
    policy                     = optional(string),
    private_dns_enabled        = optional(bool),
    resource_configuration_arn = optional(string),
    route_table_ids            = optional(set(string)),
    security_group_ids         = optional(set(string)),
    service_name               = optional(string),
    service_network_arn        = optional(string),
    service_region             = optional(string),
    subnet_configuration = optional(set(object({
      ipv4      = optional(string),
      ipv6      = optional(string),
      subnet_id = optional(string)
    }))),
    subnet_ids = optional(set(string)),
    tags       = optional(map(string)),
    tags_all   = optional(map(string)),
    timeouts = optional(object({
      create = optional(string),
      delete = optional(string),
      update = optional(string)
    })),
    vpc_endpoint_type = optional(string)
  })
}