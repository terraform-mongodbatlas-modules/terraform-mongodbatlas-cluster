output "vpc_endpoint" {
  value = {
    arn = aws_vpc_endpoint.this.arn
    cidr_blocks = aws_vpc_endpoint.this.cidr_blocks
    dns_entry = aws_vpc_endpoint.this.dns_entry
    dns_options = aws_vpc_endpoint.this.dns_options
    ip_address_type = aws_vpc_endpoint.this.ip_address_type
    network_interface_ids = aws_vpc_endpoint.this.network_interface_ids
    owner_id = aws_vpc_endpoint.this.owner_id
    policy = aws_vpc_endpoint.this.policy
    prefix_list_id = aws_vpc_endpoint.this.prefix_list_id
    private_dns_enabled = aws_vpc_endpoint.this.private_dns_enabled
    requester_managed = aws_vpc_endpoint.this.requester_managed
    route_table_ids = aws_vpc_endpoint.this.route_table_ids
    security_group_ids = aws_vpc_endpoint.this.security_group_ids
    service_region = aws_vpc_endpoint.this.service_region
    state = aws_vpc_endpoint.this.state
    subnet_ids = aws_vpc_endpoint.this.subnet_ids
    tags_all = aws_vpc_endpoint.this.tags_all
  }
}