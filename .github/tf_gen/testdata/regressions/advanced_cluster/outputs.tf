output "advanced_configuration" {
  value       = mongodbatlas_advanced_cluster.this.advanced_configuration
  description = "Additional settings for an Atlas cluster."
}

output "backup_enabled" {
  value       = mongodbatlas_advanced_cluster.this.backup_enabled
  description = "Flag that indicates whether the cluster can perform backups. If set to `true`, the cluster can perform backups. You must set this value to `true` for NVMe clusters. Backup uses [Cloud Backups](https://docs.atlas.mongodb.com/backup/cloud-backup/overview/) for dedicated clusters and [Shared Cluster Backups](https://docs.atlas.mongodb.com/backup/shared-tier/overview/) for tenant clusters. If set to `false`, the cluster doesn't use backups."
}

output "bi_connector_config" {
  value       = mongodbatlas_advanced_cluster.this.bi_connector_config
  description = "Settings needed to configure the MongoDB Connector for Business Intelligence for this cluster."
}

output "bi_connector_config_enabled" {
  value       = mongodbatlas_advanced_cluster.this.bi_connector_config == null ? null : mongodbatlas_advanced_cluster.this.bi_connector_config.enabled
  description = "Flag that indicates whether MongoDB Connector for Business Intelligence is enabled on the specified cluster."
}

output "bi_connector_config_read_preference" {
  value       = mongodbatlas_advanced_cluster.this.bi_connector_config == null ? null : mongodbatlas_advanced_cluster.this.bi_connector_config.read_preference
  description = "Data source node designated for the MongoDB Connector for Business Intelligence on MongoDB Cloud. The MongoDB Connector for Business Intelligence on MongoDB Cloud reads data from the primary, secondary, or analytics node based on your read preferences. Defaults to `ANALYTICS` node, or `SECONDARY` if there are no `ANALYTICS` nodes."
}

output "cluster_id" {
  value       = mongodbatlas_advanced_cluster.this.cluster_id
  description = "Unique 24-hexadecimal digit string that identifies the cluster."
}

output "config_server_management_mode" {
  value       = mongodbatlas_advanced_cluster.this.config_server_management_mode
  description = <<-EOT
Config Server Management Mode for creating or updating a sharded cluster.

When configured as ATLAS_MANAGED, atlas may automatically switch the cluster's config server type for optimal performance and savings.

When configured as FIXED_TO_DEDICATED, the cluster will always use a dedicated config server.
EOT
}

output "config_server_type" {
  value       = mongodbatlas_advanced_cluster.this.config_server_type
  description = "Describes a sharded cluster's config server type."
}

output "connection_strings" {
  value       = mongodbatlas_advanced_cluster.this.connection_strings
  description = "Collection of Uniform Resource Locators that point to the MongoDB database."
}

output "connection_strings_private" {
  value       = mongodbatlas_advanced_cluster.this.connection_strings == null ? null : mongodbatlas_advanced_cluster.this.connection_strings.private
  description = "Network peering connection strings for each interface Virtual Private Cloud (VPC) endpoint that you configured to connect to this cluster. This connection string uses the `mongodb+srv://` protocol. The resource returns this parameter once someone creates a network peering connection to this cluster. This protocol tells the application to look up the host seed list in the Domain Name System (DNS). This list synchronizes with the nodes in a cluster. If the connection string uses this Uniform Resource Identifier (URI) format, you don't need to append the seed list or change the URI if the nodes change. Use this URI format if your driver supports it. If it doesn't, use connectionStrings.private. For Amazon Web Services (AWS) clusters, this resource returns this parameter only if you enable custom DNS."
}

output "connection_strings_private_endpoint" {
  value       = mongodbatlas_advanced_cluster.this.connection_strings == null ? null : mongodbatlas_advanced_cluster.this.connection_strings.private_endpoint
  description = "List of private endpoint-aware connection strings that you can use to connect to this cluster through a private endpoint. This parameter returns only if you deployed a private endpoint to all regions to which you deployed this clusters' nodes."
}

output "connection_strings_private_srv" {
  value       = mongodbatlas_advanced_cluster.this.connection_strings == null ? null : mongodbatlas_advanced_cluster.this.connection_strings.private_srv
  description = "Network peering connection strings for each interface Virtual Private Cloud (VPC) endpoint that you configured to connect to this cluster. This connection string uses the `mongodb+srv://` protocol. The resource returns this parameter when someone creates a network peering connection to this cluster. This protocol tells the application to look up the host seed list in the Domain Name System (DNS). This list synchronizes with the nodes in a cluster. If the connection string uses this Uniform Resource Identifier (URI) format, you don't need to append the seed list or change the Uniform Resource Identifier (URI) if the nodes change. Use this Uniform Resource Identifier (URI) format if your driver supports it. If it doesn't, use `connectionStrings.private`. For Amazon Web Services (AWS) clusters, this parameter returns only if you [enable custom DNS](https://docs.atlas.mongodb.com/reference/api/aws-custom-dns-update/)."
}

output "connection_strings_standard" {
  value       = mongodbatlas_advanced_cluster.this.connection_strings == null ? null : mongodbatlas_advanced_cluster.this.connection_strings.standard
  description = "Public connection string that you can use to connect to this cluster. This connection string uses the `mongodb://` protocol."
}

output "connection_strings_standard_srv" {
  value       = mongodbatlas_advanced_cluster.this.connection_strings == null ? null : mongodbatlas_advanced_cluster.this.connection_strings.standard_srv
  description = "Public connection string that you can use to connect to this cluster. This connection string uses the `mongodb+srv://` protocol."
}

output "create_date" {
  value       = mongodbatlas_advanced_cluster.this.create_date
  description = "Date and time when MongoDB Cloud created this cluster. This parameter expresses its value in ISO 8601 format in UTC."
}

output "disk_size_gb" {
  value       = mongodbatlas_advanced_cluster.this.disk_size_gb
  description = <<-EOT
DEPRECATED: Storage capacity of instance data volumes expressed in gigabytes. Increase this number to add capacity.

 This value must be equal for all shards and node types.

 This value is not configurable on M0/M2/M5 clusters.

 MongoDB Cloud requires this parameter if you set **replicationSpecs**.

 If you specify a disk size below the minimum (10 GB), this parameter defaults to the minimum disk size value. 

 Storage charge calculations depend on whether you choose the default value or a custom value.

 The maximum value for disk storage cannot exceed 50 times the maximum RAM for the selected cluster. If you require more storage space, consider upgrading your cluster to a higher tier.
EOT
}

output "encryption_at_rest_provider" {
  value       = mongodbatlas_advanced_cluster.this.encryption_at_rest_provider
  description = "Cloud service provider that manages your customer keys to provide an additional layer of encryption at rest for the cluster. To enable customer key management for encryption at rest, the cluster **replicationSpecs[n].regionConfigs[m].{type}Specs.instanceSize** setting must be `M10` or higher and `\"backupEnabled\" : false` or omitted entirely."
}

output "global_cluster_self_managed_sharding" {
  value       = mongodbatlas_advanced_cluster.this.global_cluster_self_managed_sharding
  description = <<-EOT
Set this field to configure the Sharding Management Mode when creating a new Global Cluster.

When set to false, the management mode is set to Atlas-Managed Sharding. This mode fully manages the sharding of your Global Cluster and is built to provide a seamless deployment experience.

When set to true, the management mode is set to Self-Managed Sharding. This mode leaves the management of shards in your hands and is built to provide an advanced and flexible deployment experience.

This setting cannot be changed once the cluster is deployed.
EOT
}

output "mongo_db_major_version" {
  value       = mongodbatlas_advanced_cluster.this.mongo_db_major_version
  description = <<-EOT
MongoDB major version of the cluster.

On creation: Choose from the available versions of MongoDB, or leave unspecified for the current recommended default in the MongoDB Cloud platform. The recommended version is a recent Long Term Support version. The default is not guaranteed to be the most recently released version throughout the entire release cycle. For versions available in a specific project, see the linked documentation or use the API endpoint for [project LTS versions endpoint](#tag/Projects/operation/getProjectLTSVersions).

 On update: Increase version only by 1 major version at a time. If the cluster is pinned to a MongoDB feature compatibility version exactly one major version below the current MongoDB version, the MongoDB version can be downgraded to the previous major version.
EOT
}

output "mongo_db_version" {
  value       = mongodbatlas_advanced_cluster.this.mongo_db_version
  description = "Version of MongoDB that the cluster runs."
}

output "paused" {
  value       = mongodbatlas_advanced_cluster.this.paused
  description = "Flag that indicates whether the cluster is paused."
}

output "pit_enabled" {
  value       = mongodbatlas_advanced_cluster.this.pit_enabled
  description = "Flag that indicates whether the cluster uses continuous cloud backups."
}

output "redact_client_log_data" {
  value       = mongodbatlas_advanced_cluster.this.redact_client_log_data
  description = <<-EOT
Enable or disable log redaction.

This setting configures the ``mongod`` or ``mongos`` to redact any document field contents from a message accompanying a given log event before logging. This prevents the program from writing potentially sensitive data stored on the database to the diagnostic log. Metadata such as error or operation codes, line numbers, and source file names are still visible in the logs.

Use ``redactClientLogData`` in conjunction with Encryption at Rest and TLS/SSL (Transport Encryption) to assist compliance with regulatory requirements.

*Note*: changing this setting on a cluster will trigger a rolling restart as soon as the cluster is updated.
EOT
}

output "replica_set_scaling_strategy" {
  value       = mongodbatlas_advanced_cluster.this.replica_set_scaling_strategy
  description = <<-EOT
Set this field to configure the replica set scaling mode for your cluster.

By default, Atlas scales under WORKLOAD_TYPE. This mode allows Atlas to scale your analytics nodes in parallel to your operational nodes.

When configured as SEQUENTIAL, Atlas scales all nodes sequentially. This mode is intended for steady-state workloads and applications performing latency-sensitive secondary reads.

When configured as NODE_TYPE, Atlas scales your electable nodes in parallel with your read-only and analytics nodes. This mode is intended for large, dynamic workloads requiring frequent and timely cluster tier scaling. This is the fastest scaling strategy, but it might impact latency of workloads when performing extensive secondary reads.
EOT
}

output "root_cert_type" {
  value       = mongodbatlas_advanced_cluster.this.root_cert_type
  description = "Root Certificate Authority that MongoDB Cloud cluster uses. MongoDB Cloud supports Internet Security Research Group."
}

output "state_name" {
  value       = mongodbatlas_advanced_cluster.this.state_name
  description = "Human-readable label that indicates the current operating condition of this cluster."
}

output "termination_protection_enabled" {
  value       = mongodbatlas_advanced_cluster.this.termination_protection_enabled
  description = "Flag that indicates whether termination protection is enabled on the cluster. If set to `true`, MongoDB Cloud won't delete the cluster. If set to `false`, MongoDB Cloud will delete the cluster."
}

output "version_release_system" {
  value       = mongodbatlas_advanced_cluster.this.version_release_system
  description = "Method by which the cluster maintains the MongoDB versions. If value is `CONTINUOUS`, you must not specify **mongoDBMajorVersion**."
}