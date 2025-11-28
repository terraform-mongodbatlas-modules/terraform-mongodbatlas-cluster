# MongoDB Atlas Cluster Module (Public Preview)

This module simplifies the MongoDB Atlas cluster resource. Obtain more granular control by replacing simplified attributes with the standard resource attributes defined in [`mongodbatlas_advanced_cluster (provider 2.0.0)`](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs/resources/advanced_cluster).

<!-- BEGIN_TOC -->
- [Public Preview Note](#public-preview-note)
- [Disclaimer](#disclaimer)
- [Getting Started](#getting-started)
- [Getting Started Examples](#getting-started-examples)
- [Examples](#examples)
- [Cluster Topology Configuration](#cluster-topology-configuration)
- [Requirements](#requirements)
- [Providers](#providers)
- [Resources](#resources)
- [Required Inputs](#required-inputs)
- [Optional Inputs](#optional-inputs)
- [Required Variables](#required-variables)
- [Cluster Topology Option 1 - `regions` Variables](#cluster-topology-option-1---regions-variables)
- [Cluster Topology Option 2 - `replication_specs` Variables](#cluster-topology-option-2---replication_specs-variables)
- [Production Recommendations (Enabled By Default)](#production-recommendations-enabled-by-default)
- [Production Recommendations (Manually Configured)](#production-recommendations-manually-configured)
- [Optional Variables](#optional-variables)
- [Outputs](#outputs)
- [FAQ](#faq)
<!-- END_TOC -->

## Public Preview Note

The MongoDB Atlas Cluster Module (Public Preview) simplifies cluster deployments and embeds MongoDB's best practices as intelligent defaults. This preview validates that these patterns meet the needs of most workloads without constant maintenance or rework. We welcome your feedback and contributions during this preview phase. MongoDB formally supports this module from its v1 release onwards.

<!-- BEGIN_DISCLAIMER -->
## Disclaimer

One of this project's primary objectives is to provide durable modules that support non-breaking migration and upgrade paths. The v0 release (public preview) of the MongoDB Atlas Cluster Module focuses on gathering feedback and refining the design. Upgrades from v0 to v1 may not be seamless. We plan to deliver a finalized v1 release early next year with long term upgrade support.  

<!-- END_DISCLAIMER -->

## Getting Started

This section guides you through the basic steps to set up Terraform and run this module to create a new [development cluster](./examples/08_development_cluster) as a practical example.

### Pre Requirements

**NOTE**: If you are familiar with Terraform and already have a project configured in MongoDB Atlas, go to [Create a New Cluster](#create-a-new-cluster)

Perform the following steps to download and configure the tools required to create a new MongoDB Atlas development cluster:

1. Install [Terraform](https://developer.hashicorp.com/terraform/install).

2. [Sign in](https://account.mongodb.com/account/login) or [create](https://account.mongodb.com/account/register) your MongoDB Atlas Account.

3. Configure your [authentication](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs#authentication) method.

   **NOTE**: Service Accounts (SA) is the preferred authentication method. See [Grant Programatic Access to an Organization](https://www.mongodb.com/docs/atlas/configure-api-access/#grant-programmatic-access-to-an-organization) in the MongoDB Atlas documentation for detailed instructions on configuring SA access to your project.

4. Use an existing [MongoDB Atlas Project](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs/resources/project) or [create a new Atlas Project](./examples/08_development_cluster/README.md/#optionally-create-a-new-atlas-project-resource).

### Create a New Cluster

Perform the following steps to create a new cluster using the cluster module:

1. Create your Terraform configuration files.
  Ensure your files contain the code provided in this repository:
  
   - [main.tf](./examples/08_development_cluster/README.md/#code-snippet)
   - [variables.tf](./examples/08_development_cluster/variables.tf)
   - [versions.tf](examples/08_development_cluster/versions.tf)

2. Initialize Terraform.
  
    ```sh
    terraform init # download the required providers and create a `terraform.lock.hcl` file.
    ```

3. Configure your authentication environment variables.
  
    ```sh
    export MONGODB_ATLAS_CLIENT_ID="your-client-id-goes-here"
    export MONGODB_ATLAS_CLIENT_SECRET="your-client-secret-goes-here"
    ```

4. Preview your configuration to ensure it works correctly.

    ```sh
    terraform plan
    ```

5. Create your new cluster.

    ```sh
    terraform apply
    ```

   Terraform creates the new cluster in your MongoDB Atlas infrastructure.

### Clean up your configuration

Run `terraform destroy` to undo all changes that Terraform did on your infrastructure.

<!-- BEGIN_TABLES -->
## Getting Started Examples

Cluster Type | Environment | Name
--- | --- | ---
REPLICASET | Development | [Development Cluster](./examples/08_development_cluster)
SHARDED | Production | [Production Cluster with Auto Scaling](./examples/01_production_cluster_with_auto_scaling)
SHARDED | Production | [Production Cluster with Manual Scaling](./examples/02_production_cluster_with_manual_scaling)

## Examples

Cluster Type | Name
--- | ---
SHARDED | [Cluster with Analytics Nodes](./examples/03_cluster_with_analytics_nodes)
REPLICASET | [Cluster with Multi Regions Local (US_EAST_1 + US_EAST_2)](./examples/04_cluster_with_multi_regions_local)
SHARDED | [Cluster with Multi Regions Global (US+EU)](./examples/05_cluster_with_multi_regions_global)
GEOSHARDED | [Cluster with Multi Zones (GEOSHARDED)](./examples/06_cluster_with_multi_zones)
SHARDED | [Cluster with Multi Clouds (AWS+AZURE)](./examples/07_cluster_with_multi_clouds)
SHARDED | [Cluster using the `replication_specs` to define Cluster Topology](./examples/09_cluster_using_replication_specs)
GEOSHARDED | [Cluster with Multi Zone and each zone with multiple shards (Advanced)](./examples/10_cluster_with_multi_zone_multi_shards)
Multiple | [Demonstrate how to create a module "on-top" of the module with a simplified interface (cluster_size=S/M/L)](./examples/11_module_wrapper_cluster_size)
SHARDED | [Cluster with uniform SHARDED topology using `shard_count`](./examples/12_cluster_uniform_sharded_topology)

<!-- END_TABLES -->

## Cluster Topology Configuration

**For a comprehensive guide on cluster topology configuration, see [Cluster Topology Guide](./docs/cluster_topology.md), which includes detailed explanations, examples, and migration instructions.**

This module offers two mutually exclusive ways to configure cluster topology:

- [Option 1 - `regions` Variables](#cluster-topology-option-1---regions-variables)
- [Option 2 - `replication_specs` Variables](#cluster-topology-option-2---replication_specs-variables)

<!-- BEGIN_TF_DOCS -->
## Requirements

The following requirements are needed by this module:

- <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) (>= 1.9)

- <a name="requirement_mongodbatlas"></a> [mongodbatlas](#requirement\_mongodbatlas) (~> 2.0)

## Providers

The following providers are used by this module:

- <a name="provider_mongodbatlas"></a> [mongodbatlas](#provider\_mongodbatlas) (~> 2.0)

## Resources

The following resources are used by this module:

- [mongodbatlas_advanced_cluster.this](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs/resources/advanced_cluster) (resource)
- [mongodbatlas_advanced_clusters.this](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs/data-sources/advanced_clusters) (data source)

**NOTE**: The `data.mongodbatlas_advanced_clusters` is used by auto-scaled clusters to avoid unexpected plan changes when `instance_size` have updated.

<!-- BEGIN_TF_INPUTS_RAW -->
## Required Inputs

The following input variables are required:

### <a name="input_cluster_type"></a> [cluster\_type](#input\_cluster\_type)

Description: Type of the cluster that you want to create. Valid values are `REPLICASET` / `SHARDED` / `GEOSHARDED`.

Type: `string`

### <a name="input_name"></a> [name](#input\_name)

Description: Human-readable label that identifies this cluster, for example: `my-product-cluster`.

Type: `string`

### <a name="input_project_id"></a> [project\_id](#input\_project\_id)

Description: Unique 24-hexadecimal digit string that identifies your project, for example `664619d870c247237f4b86a6`. It is found listing projects in the Admin API or selecting a project in the UI and copying the path in the URL.

**NOTE**: Groups and projects are synonymous terms. Your group id is the same as your project id. For existing groups, your group/project id remains the same. The resource and corresponding endpoints use the term groups.

Type: `string`

### <a name="input_regions"></a> [regions](#input\_regions)

Description: The simplest way to define your cluster topology:
- Set `name`, for example `US_EAST_1`, see all valid [region names](https://www.mongodb.com/docs/atlas/cloud-providers-regions/).
- Set `node_count`, `node_count_read_only`, `node_count_analytics` depending on your needs.
- Set `provider_name` (AWS/AZURE/GCP) or use the "root" level `provider_name` variable if all regions share the provider\_name.
- For cluster\_type.REPLICASET: omit both `shard_number` and `zone_name`.
- For cluster\_type.SHARDED: set `shard_number` on each region or use the `shard_count` variable; do not set `zone_name`. Regions with the same `shard_number` belong to the same shard.
- For cluster\_type.GEOSHARDED: set `zone_name` on each region; optionally set `shard_number`. Regions with the same `zone_name` form one zone.

NOTE:
- The order in which region blocks are defined in this list determines their priority within each shard or zone.
  - The first region gets priority 7 (maximum), the next 6, and so on (minimum 0). For more context, see [this section of the Atlas Admin API documentation](https://www.mongodb.com/docs/api/doc/atlas-admin-api-v2/operation/operation-creategroupcluster#operation-creategroupcluster-body-application-vnd-atlas-2024-10-23-json-replicationspecs-regionconfigs-priority).
- Within a zone, shard\_numbers are specific to that zone and independent of the shard\_number in any other zones.
- `shard_number` is a variable specific to this module used to group regions within a shard and does not represent an actual value in Atlas.

Type:

```hcl
list(object({
    name                    = string
    disk_iops               = optional(number)
    disk_size_gb            = optional(number)
    ebs_volume_type         = optional(string)
    instance_size           = optional(string)
    instance_size_analytics = optional(string)
    node_count              = optional(number)
    node_count_analytics    = optional(number)
    node_count_read_only    = optional(number)
    provider_name           = optional(string)
    shard_number            = optional(number)
    zone_name               = optional(string)
  }))
```

## Optional Inputs

The following input variables are optional (have default values):

### <a name="input_accept_data_risks_and_force_replica_set_reconfig"></a> [accept\_data\_risks\_and\_force\_replica\_set\_reconfig](#input\_accept\_data\_risks\_and\_force\_replica\_set\_reconfig)

Description: If reconfiguration is necessary to regain a primary due to a regional outage, submit this field alongside your topology reconfiguration to request a new regional outage resistant topology. Forced reconfigurations during an outage of the majority of electable nodes carry a risk of data loss if replicated writes (even majority committed writes) have not been replicated to the new primary node. MongoDB Atlas docs contain more information. To proceed with an operation which carries that risk, set **acceptDataRisksAndForceReplicaSetReconfig** to the current date.

Type: `string`

Default: `null`

### <a name="input_advanced_configuration"></a> [advanced\_configuration](#input\_advanced\_configuration)

Description: Additional settings for an Atlas cluster.

Type:

```hcl
object({
    change_stream_options_pre_and_post_images_expire_after_seconds = optional(number)
    custom_openssl_cipher_config_tls12                             = optional(list(string))
    default_max_time_ms                                            = optional(number)
    default_write_concern                                          = optional(string, "majority")
    javascript_enabled                                             = optional(bool, false)
    minimum_enabled_tls_protocol                                   = optional(string, "TLS1_2")
    no_table_scan                                                  = optional(bool)
    oplog_min_retention_hours                                      = optional(number)
    oplog_size_mb                                                  = optional(number)
    sample_refresh_interval_bi_connector                           = optional(number)
    sample_size_bi_connector                                       = optional(number)
    tls_cipher_config_mode                                         = optional(string)
    transaction_lifetime_limit_seconds                             = optional(number)
  })
```

Default:

```json
{
  "default_write_concern": "majority",
  "javascript_enabled": false,
  "minimum_enabled_tls_protocol": "TLS1_2"
}
```

### <a name="input_auto_scaling"></a> [auto\_scaling](#input\_auto\_scaling)

Description: Auto scaling config for electable/read-only specs. Enabled by default with Architecture Center recommended defaults.

Type:

```hcl
object({
    compute_enabled            = optional(bool, true)
    compute_max_instance_size  = optional(string, "M200")
    compute_min_instance_size  = optional(string, "M10")
    compute_scale_down_enabled = optional(bool, true)
    disk_gb_enabled            = optional(bool, true)
  })
```

Default:

```json
{
  "compute_enabled": true,
  "compute_max_instance_size": "M200",
  "compute_min_instance_size": "M10",
  "compute_scale_down_enabled": true,
  "disk_gb_enabled": true
}
```

### <a name="input_auto_scaling_analytics"></a> [auto\_scaling\_analytics](#input\_auto\_scaling\_analytics)

Description: Auto scaling config for analytics specs.

When `auto_scaling_analytics` is `null` (default) and no manual `instance_size_analytics` is set, analytics nodes will inherit the auto-scaling configuration from the electable nodes (`auto_scaling`). This includes all settings: `compute_enabled`, `compute_max_instance_size`, `compute_min_instance_size`, `compute_scale_down_enabled`, and `disk_gb_enabled`.

When `auto_scaling_analytics` is explicitly set, it uses its own configuration. If `compute_scale_down_enabled` is not specified, it defaults to `true` (consistent with the electable nodes default behavior).

Type:

```hcl
object({
    compute_enabled            = optional(bool)
    compute_max_instance_size  = optional(string)
    compute_min_instance_size  = optional(string)
    compute_scale_down_enabled = optional(bool)
    disk_gb_enabled            = optional(bool)
  })
```

Default: `null`

### <a name="input_backup_enabled"></a> [backup\_enabled](#input\_backup\_enabled)

Description: Recommended for production clusters. Flag that indicates whether the cluster can perform backups. If set to `true`, the cluster can perform backups. You must set this value to `true` for NVMe clusters. Backup uses [Cloud Backups](https://docs.atlas.mongodb.com/backup/cloud-backup/overview/) for dedicated clusters and [Shared Cluster Backups](https://docs.atlas.mongodb.com/backup/shared-tier/overview/) for tenant clusters. If set to `false`, the cluster doesn't use backups.

Type: `bool`

Default: `true`

### <a name="input_bi_connector_config"></a> [bi\_connector\_config](#input\_bi\_connector\_config)

Description: Settings needed to configure the MongoDB Connector for Business Intelligence for this cluster.

Type:

```hcl
object({
    enabled         = optional(bool)
    read_preference = optional(string)
  })
```

Default: `null`

### <a name="input_config_server_management_mode"></a> [config\_server\_management\_mode](#input\_config\_server\_management\_mode)

Description: Config Server Management Mode for creating or updating a sharded cluster.

When configured as ATLAS\_MANAGED, atlas may automatically switch the cluster's config server type for optimal performance and savings.

When configured as FIXED\_TO\_DEDICATED, the cluster will always use a dedicated config server.

Type: `string`

Default: `null`

### <a name="input_delete_on_create_timeout"></a> [delete\_on\_create\_timeout](#input\_delete\_on\_create\_timeout)

Description: Flag that indicates whether to delete the cluster if the cluster creation times out. Default is false.

Type: `bool`

Default: `null`

### <a name="input_disk_iops"></a> [disk\_iops](#input\_disk\_iops)

Description: Only valid for AWS and Azure instances.

#### AWS  
Target IOPS (Input/Output Operations Per Second) desired for storage attached to this hardware.

Change this parameter if you:

- set `"replicationSpecs[n].regionConfigs[m].providerName" to "AWS"`.
- set `"replicationSpecs[n].regionConfigs[m].electableSpecs.instanceSize" to "M30"` or greater (not including `Mxx_NVME` tiers).

- set `"replicationSpecs[n].regionConfigs[m].electableSpecs.ebsVolumeType" to "PROVISIONED"`.

The maximum input/output operations per second (IOPS) depend on the selected **.instanceSize** and **.diskSizeGB**.  
This parameter defaults to the cluster tier's standard IOPS value.  
Changing this value impacts cluster cost.  
MongoDB Cloud enforces minimum ratios of storage capacity to system memory for given cluster tiers. This keeps cluster performance consistent with large datasets.

- Instance sizes `M10` to `M40` have a ratio of disk capacity to system memory of 60:1.
- Instance sizes greater than `M40` have a ratio of 120:1.

#### Azure  
Target throughput desired for storage attached to your Azure-provisioned cluster. Change this parameter if you:

- set `"replicationSpecs[n].regionConfigs[m].providerName" : "Azure"`.
- set `"replicationSpecs[n].regionConfigs[m].electableSpecs.instanceSize" : "M40"` or greater not including `Mxx_NVME` tiers.

The maximum input/output operations per second (IOPS) depend on the selected **.instanceSize** and **.diskSizeGB**.  
This parameter defaults to the cluster tier's standard IOPS value.  
Changing this value impacts cluster cost.

Type: `number`

Default: `null`

### <a name="input_disk_size_gb"></a> [disk\_size\_gb](#input\_disk\_size\_gb)

Description: Storage capacity of instance data volumes expressed in gigabytes. Increase this number to add capacity.

 This value must be equal for all shards and node types.

 This value is not configurable on M0/M2/M5 clusters.

 MongoDB Cloud requires this parameter if you set **replicationSpecs**.

 If you specify a disk size below the minimum (10 GB), this parameter defaults to the minimum disk size value.

 Storage charge calculations depend on whether you choose the default value or a custom value.

 The maximum value for disk storage cannot exceed 50 times the maximum RAM for the selected cluster. If you require more storage space, consider upgrading your cluster to a higher tier.

Type: `number`

Default: `null`

### <a name="input_ebs_volume_type"></a> [ebs\_volume\_type](#input\_ebs\_volume\_type)

Description: Type of storage you want to attach to your AWS-provisioned cluster.\n\n- `STANDARD` volume types can't exceed the default input/output operations per second (IOPS) rate for the selected volume size. \n\n- `PROVISIONED` volume types must fall within the allowable IOPS range for the selected volume size. You must set this value to (`PROVISIONED`) for NVMe clusters.

Type: `string`

Default: `null`

### <a name="input_encryption_at_rest_provider"></a> [encryption\_at\_rest\_provider](#input\_encryption\_at\_rest\_provider)

Description: Cloud service provider that manages your customer keys to provide an additional layer of encryption at rest for the cluster. To enable customer key management for encryption at rest, the cluster **replicationSpecs[n].regionConfigs[m].{type}Specs.instanceSize** setting must be `M10` or higher and `"backupEnabled" : false` or omitted entirely.

Type: `string`

Default: `null`

### <a name="input_global_cluster_self_managed_sharding"></a> [global\_cluster\_self\_managed\_sharding](#input\_global\_cluster\_self\_managed\_sharding)

Description: Set this field to configure the Sharding Management Mode when creating a new Global Cluster.

When set to false, the management mode is set to Atlas-Managed Sharding. This mode fully manages the sharding of your Global Cluster and is built to provide a seamless deployment experience.

When set to true, the management mode is set to Self-Managed Sharding. This mode leaves the management of shards in your hands and is built to provide an advanced and flexible deployment experience.

This setting cannot be changed once the cluster is deployed.

Type: `bool`

Default: `null`

### <a name="input_instance_size"></a> [instance\_size](#input\_instance\_size)

Description: Default instance\_size in electable/read-only specs. Only used when auto\_scaling.compute\_enabled = false. Defaults to M10 if not specified.

Type: `string`

Default: `null`

### <a name="input_instance_size_analytics"></a> [instance\_size\_analytics](#input\_instance\_size\_analytics)

Description: Default instance\_size in analytics specs. Do not set if using auto\_scaling\_analytics.

Type: `string`

Default: `null`

### <a name="input_mongo_db_major_version"></a> [mongo\_db\_major\_version](#input\_mongo\_db\_major\_version)

Description: MongoDB major version of the cluster.

On creation: Choose from the available versions of MongoDB, or leave unspecified for the current recommended default in the MongoDB Cloud platform. The recommended version is a recent Long Term Support version. The default is not guaranteed to be the most recently released version throughout the entire release cycle. For versions available in a specific project, see the linked documentation or use the API endpoint for [project LTS versions endpoint](#tag/Projects/operation/getProjectLTSVersions).

 On update: Increase version only by 1 major version at a time. If the cluster is pinned to a MongoDB feature compatibility version exactly one major version below the current MongoDB version, the MongoDB version can be downgraded to the previous major version.

Type: `string`

Default: `null`

### <a name="input_paused"></a> [paused](#input\_paused)

Description: Flag that indicates whether the cluster is paused.

Type: `bool`

Default: `null`

### <a name="input_pinned_fcv"></a> [pinned\_fcv](#input\_pinned\_fcv)

Description: Pins the Feature Compatibility Version (FCV) to the current MongoDB version with a provided expiration date. To unpin the FCV the `pinned_fcv` attribute must be removed. This operation can take several minutes as the request processes through the MongoDB data plane. Once FCV is unpinned it will not be possible to downgrade the `mongo_db_major_version`. It is advised that updates to `pinned_fcv` are done isolated from other cluster changes. If a plan contains multiple changes, the FCV change will be applied first. If FCV is unpinned past the expiration date the `pinned_fcv` attribute must be removed. The following [knowledge hub article](https://kb.corp.mongodb.com/article/000021785/) and [FCV documentation](https://www.mongodb.com/docs/atlas/tutorial/major-version-change/#manage-feature-compatibility--fcv--during-upgrades) can be referenced for more details.

Type:

```hcl
object({
    expiration_date = string
  })
```

Default: `null`

### <a name="input_pit_enabled"></a> [pit\_enabled](#input\_pit\_enabled)

Description: Recommended for production clusters. Flag that indicates whether the cluster uses continuous cloud backups.

Type: `bool`

Default: `true`

### <a name="input_provider_name"></a> [provider\_name](#input\_provider\_name)

Description: AWS/AZURE/GCP, setting this on the root level, will use it inside of each `region`.

Type: `string`

Default: `null`

### <a name="input_redact_client_log_data"></a> [redact\_client\_log\_data](#input\_redact\_client\_log\_data)

Description: Enable or disable log redaction.

This setting configures the `mongod` or `mongos` to redact any document field contents from a message accompanying a given log event before logging.This prevents the program from writing potentially sensitive data stored on the database to the diagnostic log. Metadata such as error or operation codes, line numbers, and source file names are still visible in the logs.

Use `redactClientLogData` in conjunction with Encryption at Rest and TLS/SSL (Transport Encryption) to assist compliance with regulatory requirements.

*Note*: changing this setting on a cluster will trigger a rolling restart as soon as the cluster is updated.

Type: `bool`

Default: `true`

### <a name="input_replica_set_scaling_strategy"></a> [replica\_set\_scaling\_strategy](#input\_replica\_set\_scaling\_strategy)

Description: Set this field to configure the replica set scaling mode for your cluster.

By default, Atlas scales under WORKLOAD\_TYPE. This mode allows Atlas to scale your analytics nodes in parallel to your operational nodes.

When configured as SEQUENTIAL, Atlas scales all nodes sequentially. This mode is intended for steady-state workloads and applications performing latency-sensitive secondary reads.

Type: `string`

Default: `null`

### <a name="input_replication_specs"></a> [replication\_specs](#input\_replication\_specs)

Description: List of settings that configure your cluster regions. This array has one object per shard representing node configurations in each shard. For replica sets there is only one object representing node configurations.

Type:

```hcl
list(object({
    region_configs = list(object({
      analytics_auto_scaling = optional(object({
        compute_enabled            = optional(bool)
        compute_max_instance_size  = optional(string)
        compute_min_instance_size  = optional(string)
        compute_scale_down_enabled = optional(bool)
        disk_gb_enabled            = optional(bool)
      }))
      analytics_specs = optional(object({
        disk_iops       = optional(number)
        disk_size_gb    = optional(number)
        ebs_volume_type = optional(string)
        instance_size   = optional(string)
        node_count      = optional(number)
      }))
      auto_scaling = optional(object({
        compute_enabled            = optional(bool)
        compute_max_instance_size  = optional(string)
        compute_min_instance_size  = optional(string)
        compute_scale_down_enabled = optional(bool)
        disk_gb_enabled            = optional(bool)
      }))
      backing_provider_name = optional(string)
      electable_specs = optional(object({
        disk_iops       = optional(number)
        disk_size_gb    = optional(number)
        ebs_volume_type = optional(string)
        instance_size   = optional(string)
        node_count      = optional(number)
      }))
      priority      = number
      provider_name = string
      read_only_specs = optional(object({
        disk_iops       = optional(number)
        disk_size_gb    = optional(number)
        ebs_volume_type = optional(string)
        instance_size   = optional(string)
        node_count      = optional(number)
      }))
      region_name = string
    }))
    zone_name = optional(string)
  }))
```

Default: `[]`

### <a name="input_retain_backups_enabled"></a> [retain\_backups\_enabled](#input\_retain\_backups\_enabled)

Description: Recommended for production clusters. Flag that indicates whether to retain backup snapshots for the deleted dedicated cluster.

Type: `bool`

Default: `true`

### <a name="input_root_cert_type"></a> [root\_cert\_type](#input\_root\_cert\_type)

Description: Root Certificate Authority that MongoDB Cloud cluster uses. MongoDB Cloud supports Internet Security Research Group.

Type: `string`

Default: `null`

### <a name="input_shard_count"></a> [shard\_count](#input\_shard\_count)

Description: Number of shards for SHARDED clusters.

- When set, all shards share the same region topology (each shard gets the same regions list).
- Do NOT set regions[*].shard\_number when shard\_count is set (they are mutually exclusive).
- When unset, you must set regions[*].shard\_number on every region to explicitly group regions into shards.

Type: `number`

Default: `null`

### <a name="input_tags"></a> [tags](#input\_tags)

Description: Map that contains key-value pairs between 1 to 255 characters in length for tagging and categorizing the cluster.  
We recommend setting:  
Department, team name, application name, environment, version, email contact, criticality.   
These values can be used for:
- Billing.
- Data classification.
- Regional compliance requirements for audit and governance purposes.

Type: `map(string)`

Default: `{}`

### <a name="input_termination_protection_enabled"></a> [termination\_protection\_enabled](#input\_termination\_protection\_enabled)

Description: Recommended for production clusters. Flag that indicates whether termination protection is enabled on the cluster. If set to `true`, MongoDB Cloud won't delete the cluster. If set to `false`, MongoDB Cloud will delete the cluster.

Type: `bool`

Default: `null`

### <a name="input_timeouts"></a> [timeouts](#input\_timeouts)

Description: Timeouts for create/update/delete operations.

Type:

```hcl
object({
    create = optional(string)
    delete = optional(string)
    update = optional(string)
  })
```

Default: `null`

### <a name="input_version_release_system"></a> [version\_release\_system](#input\_version\_release\_system)

Description: Method by which the cluster maintains the MongoDB versions. If value is `CONTINUOUS`, you must not specify **mongoDBMajorVersion**.

Type: `string`

Default: `null`
<!-- END_TF_INPUTS_RAW -->

<!-- BEGIN_GENERATED_INPUTS -->
## Required Variables

### project_id

Description: Unique 24-hexadecimal digit string that identifies your project, for example `664619d870c247237f4b86a6`. It is found listing projects in the Admin API or selecting a project in the UI and copying the path in the URL.
**NOTE**: Groups and projects are synonymous terms. Your group id is the same as your project id. For existing groups, your group/project id remains the same. The resource and corresponding endpoints use the term groups.

Type: `string`

### name

Description: Human-readable label that identifies this cluster, for example: `my-product-cluster`.

Type: `string`

### cluster_type

Description: Type of the cluster that you want to create. Valid values are `REPLICASET` / `SHARDED` / `GEOSHARDED`.

Type: `string`


## Cluster Topology Option 1 - `regions` Variables

### regions

Description: The simplest way to define your cluster topology:
- Set `name`, for example `US_EAST_1`, see all valid [region names](https://www.mongodb.com/docs/atlas/cloud-providers-regions/).
- Set `node_count`, `node_count_read_only`, `node_count_analytics` depending on your needs.
- Set `provider_name` (AWS/AZURE/GCP) or use the "root" level `provider_name` variable if all regions share the provider\_name.
- For cluster\_type.REPLICASET: omit both `shard_number` and `zone_name`.
- For cluster\_type.SHARDED: set `shard_number` on each region or use the `shard_count` variable; do not set `zone_name`. Regions with the same `shard_number` belong to the same shard.
- For cluster\_type.GEOSHARDED: set `zone_name` on each region; optionally set `shard_number`. Regions with the same `zone_name` form one zone.
NOTE:
- The order in which region blocks are defined in this list determines their priority within each shard or zone.
  - The first region gets priority 7 (maximum), the next 6, and so on (minimum 0). For more context, see [this section of the Atlas Admin API documentation](https://www.mongodb.com/docs/api/doc/atlas-admin-api-v2/operation/operation-creategroupcluster#operation-creategroupcluster-body-application-vnd-atlas-2024-10-23-json-replicationspecs-regionconfigs-priority).
- Within a zone, shard\_numbers are specific to that zone and independent of the shard\_number in any other zones.
- `shard_number` is a variable specific to this module used to group regions within a shard and does not represent an actual value in Atlas.

### provider_name

Description: AWS/AZURE/GCP, setting this on the root level, will use it inside of each `region`.

Type: `string`

Default: `null`

### shard_count

Description: Number of shards for SHARDED clusters.
- When set, all shards share the same region topology (each shard gets the same regions list).
- Do NOT set regions[*].shard\_number when shard\_count is set (they are mutually exclusive).
- When unset, you must set regions[*].shard\_number on every region to explicitly group regions into shards.

Type: `number`

Default: `null`


### Auto Scaling

#### auto_scaling

Description: Auto scaling config for electable/read-only specs. Enabled by default with Architecture Center recommended defaults.

#### auto_scaling_analytics

Description: Auto scaling config for analytics specs.
When `auto_scaling_analytics` is `null` (default) and no manual `instance_size_analytics` is set, analytics nodes will inherit the auto-scaling configuration from the electable nodes (`auto_scaling`). This includes all settings: `compute_enabled`, `compute_max_instance_size`, `compute_min_instance_size`, `compute_scale_down_enabled`, and `disk_gb_enabled`.
When `auto_scaling_analytics` is explicitly set, it uses its own configuration. If `compute_scale_down_enabled` is not specified, it defaults to `true` (consistent with the electable nodes default behavior).

Default: `null`


### Manual Scaling

#### instance_size

Description: Default instance\_size in electable/read-only specs. Only used when auto\_scaling.compute\_enabled = false. Defaults to M10 if not specified.

Type: `string`

Default: `null`

#### instance_size_analytics

Description: Default instance\_size in analytics specs. Do not set if using auto\_scaling\_analytics.

Type: `string`

Default: `null`

#### disk_size_gb

Description: Storage capacity of instance data volumes expressed in gigabytes. Increase this number to add capacity.
 This value must be equal for all shards and node types.
 This value is not configurable on M0/M2/M5 clusters.
 MongoDB Cloud requires this parameter if you set **replicationSpecs**.
 If you specify a disk size below the minimum (10 GB), this parameter defaults to the minimum disk size value.
 Storage charge calculations depend on whether you choose the default value or a custom value.
 The maximum value for disk storage cannot exceed 50 times the maximum RAM for the selected cluster. If you require more storage space, consider upgrading your cluster to a higher tier.

Type: `number`

Default: `null`

#### disk_iops

Description: Only valid for AWS and Azure instances.
#### AWS
Target IOPS (Input/Output Operations Per Second) desired for storage attached to this hardware.
Change this parameter if you:
- set `"replicationSpecs[n].regionConfigs[m].providerName" to "AWS"`.
- set `"replicationSpecs[n].regionConfigs[m].electableSpecs.instanceSize" to "M30"` or greater (not including `Mxx_NVME` tiers).
- set `"replicationSpecs[n].regionConfigs[m].electableSpecs.ebsVolumeType" to "PROVISIONED"`.
The maximum input/output operations per second (IOPS) depend on the selected **.instanceSize** and **.diskSizeGB**.
This parameter defaults to the cluster tier's standard IOPS value.
Changing this value impacts cluster cost.
MongoDB Cloud enforces minimum ratios of storage capacity to system memory for given cluster tiers. This keeps cluster performance consistent with large datasets.
- Instance sizes `M10` to `M40` have a ratio of disk capacity to system memory of 60:1.
- Instance sizes greater than `M40` have a ratio of 120:1.
#### Azure
Target throughput desired for storage attached to your Azure-provisioned cluster. Change this parameter if you:
- set `"replicationSpecs[n].regionConfigs[m].providerName" : "Azure"`.
- set `"replicationSpecs[n].regionConfigs[m].electableSpecs.instanceSize" : "M40"` or greater not including `Mxx_NVME` tiers.
The maximum input/output operations per second (IOPS) depend on the selected **.instanceSize** and **.diskSizeGB**.
This parameter defaults to the cluster tier's standard IOPS value.
Changing this value impacts cluster cost.

Type: `number`

Default: `null`

#### ebs_volume_type

Description: Type of storage you want to attach to your AWS-provisioned cluster.\n\n- `STANDARD` volume types can't exceed the default input/output operations per second (IOPS) rate for the selected volume size. \n\n- `PROVISIONED` volume types must fall within the allowable IOPS range for the selected volume size. You must set this value to (`PROVISIONED`) for NVMe clusters.

Type: `string`

Default: `null`


## Cluster Topology Option 2 - `replication_specs` Variables

### replication_specs

Description: List of settings that configure your cluster regions. This array has one object per shard representing node configurations in each shard. For replica sets there is only one object representing node configurations.

Default: `[]`


## Production Recommendations (Enabled By Default)

### advanced_configuration

Description: Additional settings for an Atlas cluster.

### backup_enabled

Description: Recommended for production clusters. Flag that indicates whether the cluster can perform backups. If set to `true`, the cluster can perform backups. You must set this value to `true` for NVMe clusters. Backup uses [Cloud Backups](https://docs.atlas.mongodb.com/backup/cloud-backup/overview/) for dedicated clusters and [Shared Cluster Backups](https://docs.atlas.mongodb.com/backup/shared-tier/overview/) for tenant clusters. If set to `false`, the cluster doesn't use backups.

Type: `bool`

Default: `true`

### pit_enabled

Description: Recommended for production clusters. Flag that indicates whether the cluster uses continuous cloud backups.

Type: `bool`

Default: `true`

### retain_backups_enabled

Description: Recommended for production clusters. Flag that indicates whether to retain backup snapshots for the deleted dedicated cluster.

Type: `bool`

Default: `true`


## Production Recommendations (Manually Configured)

### encryption_at_rest_provider

Description: Cloud service provider that manages your customer keys to provide an additional layer of encryption at rest for the cluster. To enable customer key management for encryption at rest, the cluster **replicationSpecs[n].regionConfigs[m].{type}Specs.instanceSize** setting must be `M10` or higher and `"backupEnabled" : false` or omitted entirely.

Type: `string`

Default: `null`

### redact_client_log_data

Description: Enable or disable log redaction.
This setting configures the `mongod` or `mongos` to redact any document field contents from a message accompanying a given log event before logging.This prevents the program from writing potentially sensitive data stored on the database to the diagnostic log. Metadata such as error or operation codes, line numbers, and source file names are still visible in the logs.
Use `redactClientLogData` in conjunction with Encryption at Rest and TLS/SSL (Transport Encryption) to assist compliance with regulatory requirements.
*Note*: changing this setting on a cluster will trigger a rolling restart as soon as the cluster is updated.

Type: `bool`

Default: `true`

### tags

Description: Map that contains key-value pairs between 1 to 255 characters in length for tagging and categorizing the cluster.
We recommend setting:
Department, team name, application name, environment, version, email contact, criticality.
These values can be used for:
- Billing.
- Data classification.
- Regional compliance requirements for audit and governance purposes.

Type: `map(string)`

Default: `{}`

### termination_protection_enabled

Description: Recommended for production clusters. Flag that indicates whether termination protection is enabled on the cluster. If set to `true`, MongoDB Cloud won't delete the cluster. If set to `false`, MongoDB Cloud will delete the cluster.

Type: `bool`

Default: `null`


## Optional Variables

_No variables in this section yet._
<!-- END_GENERATED_INPUTS -->


## Outputs

The following outputs are exported:

### <a name="output_cluster_id"></a> [cluster\_id](#output\_cluster\_id)

Description: Unique 24-hexadecimal digit string that identifies the cluster.

### <a name="output_cluster_name"></a> [cluster\_name](#output\_cluster\_name)

Description: MongoDB Atlas cluster name.

### <a name="output_config_server_type"></a> [config\_server\_type](#output\_config\_server\_type)

Description: Describes a sharded cluster's config server type.

### <a name="output_connection_strings"></a> [connection\_strings](#output\_connection\_strings)

Description: Collection of Uniform Resource Locators that point to the MongoDB database.

### <a name="output_create_date"></a> [create\_date](#output\_create\_date)

Description: Date and time when MongoDB Cloud created this cluster. This parameter expresses its value in ISO 8601 format in UTC.

### <a name="output_mongo_db_version"></a> [mongo\_db\_version](#output\_mongo\_db\_version)

Description: Version of MongoDB that the cluster runs.

### <a name="output_state_name"></a> [state\_name](#output\_state\_name)

Description: Human-readable label that indicates the current operating condition of this cluster.
<!-- END_TF_DOCS -->

## FAQ

### Why two options for Cluster Topology?

The module provides two approaches to accommodate different user needs and migration paths:

**Simplified Configuration (`regions`):**

- Recommended for new deployments and most use cases
- Offers a flat, intuitive schema that's easier to understand and maintain
- Automatically generates the complex `replication_specs` structure
- Supports auto-scaling with managed instance size properties
- Includes helpful abstractions like `shard_count` for uniform topologies

**Direct Configuration (`replication_specs`):**

- Useful for advanced configurations not yet abstracted by simplified variables
- Provides full control using the native provider schema
- Easier migration path from existing `mongodbatlas_advanced_cluster` resources
- Ideal for users already familiar with the resource structure

📖 **For detailed guidance on when to use each approach, see the [Cluster Topology Guide](./docs/cluster_topology.md)**

### Why does this module require Terraform 1.9+ when the provider supports 1.7.x+?

This module requires Terraform 1.9+ due to the use of cross-variable validation references, which are only supported in Terraform 1.9 and later. While the [MongoDB Atlas Provider](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs#hashicorp-terraform-version-compatibility-matrix) supports Terraform 1.7.x+, this module's validation patterns require 1.9+.

See [Terraform Version Requirements](./docs/terraform_version_requirements.md) for detailed explanation.

### What is the `provider_meta "mongodbatlas"` doing?

- This block allows us to track the usage of this module by updating the User-Agent of requests to Atlas, for example:
  - `User-Agent: terraform-provider-mongodbatlas/2.1.0 Terraform/1.13.1 module_name/cluster module_version/0.1.0`
- Note: We **do not** send any configuration-specific values, only these values to help us track feature adoption.
- You can use `export TF_LOG=debug` to see the API requests with headers and their responses.
