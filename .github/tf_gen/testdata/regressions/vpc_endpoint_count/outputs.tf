output "arn" {
  value = aws_vpc_endpoint.this[0].arn
}

output "cidr_blocks" {
  value = aws_vpc_endpoint.this[0].cidr_blocks
}

output "dns_entry" {
  value = aws_vpc_endpoint.this[0].dns_entry
}

output "dns_options_dns_record_ip_type" {
  value = aws_vpc_endpoint.this[0].dns_options == null ? null : aws_vpc_endpoint.this[0].dns_options[*].dns_record_ip_type
}

output "id" {
  value = aws_vpc_endpoint.this[0].id
}

output "ip_address_type" {
  value = aws_vpc_endpoint.this[0].ip_address_type
}

output "network_interface_ids" {
  value = aws_vpc_endpoint.this[0].network_interface_ids
}

output "owner_id" {
  value = aws_vpc_endpoint.this[0].owner_id
}

output "policy" {
  value = aws_vpc_endpoint.this[0].policy
}

output "prefix_list_id" {
  value = aws_vpc_endpoint.this[0].prefix_list_id
}

output "private_dns_enabled" {
  value = aws_vpc_endpoint.this[0].private_dns_enabled
}

output "requester_managed" {
  value = aws_vpc_endpoint.this[0].requester_managed
}

output "route_table_ids" {
  value = aws_vpc_endpoint.this[0].route_table_ids
}

output "security_group_ids" {
  value = aws_vpc_endpoint.this[0].security_group_ids
}

output "service_region" {
  value = aws_vpc_endpoint.this[0].service_region
}

output "state" {
  value = aws_vpc_endpoint.this[0].state
}

output "subnet_ids" {
  value = aws_vpc_endpoint.this[0].subnet_ids
}

output "tags_all" {
  value = aws_vpc_endpoint.this[0].tags_all
}