output "arn" {
  value = length(aws_vpc_endpoint.this) > 0 ? aws_vpc_endpoint.this[0].arn : null
}

output "cidr_blocks" {
  value = length(aws_vpc_endpoint.this) > 0 ? aws_vpc_endpoint.this[0].cidr_blocks : null
}

output "dns_entry" {
  value = length(aws_vpc_endpoint.this) > 0 ? aws_vpc_endpoint.this[0].dns_entry : null
}

output "dns_options_dns_record_ip_type" {
  value = length(aws_vpc_endpoint.this) > 0 && aws_vpc_endpoint.this[0].dns_options != null ? aws_vpc_endpoint.this[0].dns_options[*].dns_record_ip_type : null
}

output "id" {
  value = length(aws_vpc_endpoint.this) > 0 ? aws_vpc_endpoint.this[0].id : null
}

output "ip_address_type" {
  value = length(aws_vpc_endpoint.this) > 0 ? aws_vpc_endpoint.this[0].ip_address_type : null
}

output "network_interface_ids" {
  value = length(aws_vpc_endpoint.this) > 0 ? aws_vpc_endpoint.this[0].network_interface_ids : null
}

output "owner_id" {
  value = length(aws_vpc_endpoint.this) > 0 ? aws_vpc_endpoint.this[0].owner_id : null
}

output "policy" {
  value = length(aws_vpc_endpoint.this) > 0 ? aws_vpc_endpoint.this[0].policy : null
}

output "prefix_list_id" {
  value = length(aws_vpc_endpoint.this) > 0 ? aws_vpc_endpoint.this[0].prefix_list_id : null
}

output "private_dns_enabled" {
  value = length(aws_vpc_endpoint.this) > 0 ? aws_vpc_endpoint.this[0].private_dns_enabled : null
}

output "requester_managed" {
  value = length(aws_vpc_endpoint.this) > 0 ? aws_vpc_endpoint.this[0].requester_managed : null
}

output "route_table_ids" {
  value = length(aws_vpc_endpoint.this) > 0 ? aws_vpc_endpoint.this[0].route_table_ids : null
}

output "security_group_ids" {
  value = length(aws_vpc_endpoint.this) > 0 ? aws_vpc_endpoint.this[0].security_group_ids : null
}

output "service_region" {
  value = length(aws_vpc_endpoint.this) > 0 ? aws_vpc_endpoint.this[0].service_region : null
}

output "state" {
  value = length(aws_vpc_endpoint.this) > 0 ? aws_vpc_endpoint.this[0].state : null
}

output "subnet_ids" {
  value = length(aws_vpc_endpoint.this) > 0 ? aws_vpc_endpoint.this[0].subnet_ids : null
}

output "tags_all" {
  value = length(aws_vpc_endpoint.this) > 0 ? aws_vpc_endpoint.this[0].tags_all : null
}