resource "aws_vpc_endpoint" "this" {
  auto_accept                = var.aws_vpc_endpoint.auto_accept
  ip_address_type            = var.aws_vpc_endpoint.ip_address_type
  policy                     = var.aws_vpc_endpoint.policy
  private_dns_enabled        = var.aws_vpc_endpoint.private_dns_enabled
  resource_configuration_arn = var.aws_vpc_endpoint.resource_configuration_arn
  route_table_ids            = var.aws_vpc_endpoint.route_table_ids
  security_group_ids         = var.aws_vpc_endpoint.security_group_ids
  service_name               = var.aws_vpc_endpoint.service_name
  service_network_arn        = var.aws_vpc_endpoint.service_network_arn
  service_region             = var.aws_vpc_endpoint.service_region
  subnet_ids                 = var.aws_vpc_endpoint.subnet_ids
  tags                       = var.aws_vpc_endpoint.tags
  tags_all                   = var.aws_vpc_endpoint.tags_all
  vpc_endpoint_type          = var.aws_vpc_endpoint.vpc_endpoint_type
  vpc_id                     = var.aws_vpc_endpoint.vpc_id

  dynamic "dns_options" {
    for_each = var.aws_vpc_endpoint.dns_options == null ? [] : [var.aws_vpc_endpoint.dns_options]
    content {
      dns_record_ip_type                             = dns_options.value.dns_record_ip_type
      private_dns_only_for_inbound_resolver_endpoint = dns_options.value.private_dns_only_for_inbound_resolver_endpoint
    }
  }

  dynamic "subnet_configuration" {
    for_each = var.aws_vpc_endpoint.subnet_configuration == null ? [] : var.aws_vpc_endpoint.subnet_configuration
    content {
      ipv4      = subnet_configuration.value.ipv4
      ipv6      = subnet_configuration.value.ipv6
      subnet_id = subnet_configuration.value.subnet_id
    }
  }

  dynamic "timeouts" {
    for_each = var.aws_vpc_endpoint.timeouts == null ? [] : [var.aws_vpc_endpoint.timeouts]
    content {
      create = timeouts.value.create
      delete = timeouts.value.delete
      update = timeouts.value.update
    }
  }
}