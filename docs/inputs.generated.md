## Required Variables

| Name | Description | Type | Default | Required |
| --- | --- | --- | --- | --- |
| `cluster_type` | Description: Type of the cluster that you want to create. Valid values are `REPLICASET` / `SHARDED` / `GEOSHARDED`. | ``string`` | `null` | yes |
| `name` | Description: Human-readable label that identifies this cluster, for example: `my-product-cluster`. | ``string`` | `null` | yes |
| `project_id` | Description: Unique 24-hexadecimal digit string that identifies your project, for example `664619d870c247237f4b86a6`. It is found listing projects in the Admin API or selecting a project in the UI and copying the path in the URL. **NOTE**: Groups and projects are synonymous terms. Your group id is the same as your project id. For existing groups, your group/project id remains the same. The resource and corresponding endpoints use the term groups. | ``string`` | `null` | yes |

## Cluster Topology Option 1 - `regions` Variables

| Name | Description | Type | Default | Required |
| --- | --- | --- | --- | --- |
| `regions` | Description: The simplest way to define your cluster topology: - Set `name`, for example `US_EAST_1`, see all valid [region names](https://www.mongodb.com/docs/atlas/cloud-providers-regions/). - Set `node_count`, `node_count_read_only`, `node_count_analytics` depending on your needs. - Set `provider_name` (AWS/AZURE/GCP) or use the "root" level `provider_name` variable if all regions share the provider\_name. - For cluster\_type.REPLICASET: omit both `shard_number` and `zone_name`. - For cluster\_type.SHARDED: set `shard_number` on each region or use the `shard_count` variable; do not set `zone_name`. Regions with the same `shard_number` belong to the same shard. - For cluster\_type.GEOSHARDED: set `zone_name` on each region; optionally set `shard_number`. Regions with the same `zone_name` form one zone. NOTE: - The order in which region blocks are defined in this list determines their priority within each shard or zone. - The first region gets priority 7 (maximum), the next 6, and so on (minimum 0). For more context, see [this section of the Atlas Admin API documentation](https://www.mongodb.com/docs/api/doc/atlas-admin-api-v2/operation/operation-creategroupcluster#operation-creategroupcluster-body-application-vnd-atlas-2024-10-23-json-replicationspecs-regionconfigs-priority). - Within a zone, shard\_numbers are specific to that zone and independent of the shard\_number in any other zones. - `shard_number` is a variable specific to this module used to group regions within a shard and does not represent an actual value in Atlas. | `` | `null` | yes |
| `provider_name` | Description: AWS/AZURE/GCP, setting this on the root level, will use it inside of each `region`. | ``string`` | `null` | no |
| `shard_count` | Description: Number of shards for SHARDED clusters. - When set, all shards share the same region topology (each shard gets the same regions list). - Do NOT set regions[*].shard\_number when shard\_count is set (they are mutually exclusive). - When unset, you must set regions[*].shard\_number on every region to explicitly group regions into shards. | ``number`` | `null` | no |

### Auto Scaling

| Name | Description | Type | Default | Required |
| --- | --- | --- | --- | --- |
| `auto_scaling` | Description: Auto scaling config for electable/read-only specs. Enabled by default with Architecture Center recommended defaults. | `` | `null` | no |
| `auto_scaling_analytics` | Description: Auto scaling config for analytics specs. When `auto_scaling_analytics` is `null` (default) and no manual `instance_size_analytics` is set, analytics nodes will inherit the auto-scaling configuration from the electable nodes (`auto_scaling`). This includes all settings: `compute_enabled`, `compute_max_instance_size`, `compute_min_instance_size`, `compute_scale_down_enabled`, and `disk_gb_enabled`. When `auto_scaling_analytics` is explicitly set, it uses its own configuration. If `compute_scale_down_enabled` is not specified, it defaults to `true` (consistent with the electable nodes default behavior). | `` | `null` | no |

### Manual Scaling

| Name | Description | Type | Default | Required |
| --- | --- | --- | --- | --- |
| `disk_iops` | Description: Only valid for AWS and Azure instances. #### AWS Target IOPS (Input/Output Operations Per Second) desired for storage attached to this hardware. Change this parameter if you: - set `"replicationSpecs[n].regionConfigs[m].providerName" to "AWS"`. - set `"replicationSpecs[n].regionConfigs[m].electableSpecs.instanceSize" to "M30"` or greater (not including `Mxx_NVME` tiers). - set `"replicationSpecs[n].regionConfigs[m].electableSpecs.ebsVolumeType" to "PROVISIONED"`. The maximum input/output operations per second (IOPS) depend on the selected **.instanceSize** and **.diskSizeGB**. This parameter defaults to the cluster tier's standard IOPS value. Changing this value impacts cluster cost. MongoDB Cloud enforces minimum ratios of storage capacity to system memory for given cluster tiers. This keeps cluster performance consistent with large datasets. - Instance sizes `M10` to `M40` have a ratio of disk capacity to system memory of 60:1. - Instance sizes greater than `M40` have a ratio of 120:1. #### Azure Target throughput desired for storage attached to your Azure-provisioned cluster. Change this parameter if you: - set `"replicationSpecs[n].regionConfigs[m].providerName" : "Azure"`. - set `"replicationSpecs[n].regionConfigs[m].electableSpecs.instanceSize" : "M40"` or greater not including `Mxx_NVME` tiers. The maximum input/output operations per second (IOPS) depend on the selected **.instanceSize** and **.diskSizeGB**. This parameter defaults to the cluster tier's standard IOPS value. Changing this value impacts cluster cost. | ``number`` | `null` | no |
| `disk_size_gb` | Description: Storage capacity of instance data volumes expressed in gigabytes. Increase this number to add capacity. This value must be equal for all shards and node types. This value is not configurable on M0/M2/M5 clusters. MongoDB Cloud requires this parameter if you set **replicationSpecs**. If you specify a disk size below the minimum (10 GB), this parameter defaults to the minimum disk size value. Storage charge calculations depend on whether you choose the default value or a custom value. The maximum value for disk storage cannot exceed 50 times the maximum RAM for the selected cluster. If you require more storage space, consider upgrading your cluster to a higher tier. | ``number`` | `null` | no |
| `ebs_volume_type` | Description: Type of storage you want to attach to your AWS-provisioned cluster.\n\n- `STANDARD` volume types can't exceed the default input/output operations per second (IOPS) rate for the selected volume size. \n\n- `PROVISIONED` volume types must fall within the allowable IOPS range for the selected volume size. You must set this value to (`PROVISIONED`) for NVMe clusters. | ``string`` | `null` | no |
| `instance_size` | Description: Default instance\_size in electable/read-only specs. Only used when auto\_scaling.compute\_enabled = false. Defaults to M10 if not specified. | ``string`` | `null` | no |
| `instance_size_analytics` | Description: Default instance\_size in analytics specs. Do not set if using auto\_scaling\_analytics. | ``string`` | `null` | no |

## Cluster Topology Option 2 - `replication_specs` Variables

| Name | Description | Type | Default | Required |
| --- | --- | --- | --- | --- |
| `replication_specs` | Description: List of settings that configure your cluster regions. This array has one object per shard representing node configurations in each shard. For replica sets there is only one object representing node configurations. | `` | `[]` | no |

## Production Recommendations (Enabled By Default)

| Name | Description | Type | Default | Required |
| --- | --- | --- | --- | --- |
| `advanced_configuration` | Description: Additional settings for an Atlas cluster. | `` | `null` | no |
| `backup_enabled` | Description: Recommended for production clusters. Flag that indicates whether the cluster can perform backups. If set to `true`, the cluster can perform backups. You must set this value to `true` for NVMe clusters. Backup uses [Cloud Backups](https://docs.atlas.mongodb.com/backup/cloud-backup/overview/) for dedicated clusters and [Shared Cluster Backups](https://docs.atlas.mongodb.com/backup/shared-tier/overview/) for tenant clusters. If set to `false`, the cluster doesn't use backups. | ``bool`` | `true` | no |
| `pit_enabled` | Description: Recommended for production clusters. Flag that indicates whether the cluster uses continuous cloud backups. | ``bool`` | `true` | no |
| `retain_backups_enabled` | Description: Recommended for production clusters. Flag that indicates whether to retain backup snapshots for the deleted dedicated cluster. | ``bool`` | `true` | no |

## Production Recommendations (Manually Configured)

| Name | Description | Type | Default | Required |
| --- | --- | --- | --- | --- |
| `encryption_at_rest_provider` | Description: Cloud service provider that manages your customer keys to provide an additional layer of encryption at rest for the cluster. To enable customer key management for encryption at rest, the cluster **replicationSpecs[n].regionConfigs[m].{type}Specs.instanceSize** setting must be `M10` or higher and `"backupEnabled" : false` or omitted entirely. | ``string`` | `null` | no |
| `redact_client_log_data` | Description: Enable or disable log redaction. This setting configures the `mongod` or `mongos` to redact any document field contents from a message accompanying a given log event before logging.This prevents the program from writing potentially sensitive data stored on the database to the diagnostic log. Metadata such as error or operation codes, line numbers, and source file names are still visible in the logs. Use `redactClientLogData` in conjunction with Encryption at Rest and TLS/SSL (Transport Encryption) to assist compliance with regulatory requirements. *Note*: changing this setting on a cluster will trigger a rolling restart as soon as the cluster is updated. | ``bool`` | `true` | no |
| `tags` | Description: Map that contains key-value pairs between 1 to 255 characters in length for tagging and categorizing the cluster. We recommend setting: Department, team name, application name, environment, version, email contact, criticality. These values can be used for: - Billing. - Data classification. - Regional compliance requirements for audit and governance purposes. | ``map(string)`` | `{}` | no |
| `termination_protection_enabled` | Description: Recommended for production clusters. Flag that indicates whether termination protection is enabled on the cluster. If set to `true`, MongoDB Cloud won't delete the cluster. If set to `false`, MongoDB Cloud will delete the cluster. | ``bool`` | `null` | no |

## Optional Variables

_No variables in this section yet._
