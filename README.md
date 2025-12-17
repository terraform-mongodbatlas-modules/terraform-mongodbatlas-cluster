# MongoDB Atlas Cluster Module (Public Preview)

This module simplifies the MongoDB Atlas cluster resource. Obtain more granular control by replacing simplified attributes with the standard resource attributes defined in [`mongodbatlas_advanced_cluster (provider 2.0.0)`](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs/resources/advanced_cluster).

<!-- BEGIN_TOC -->
<!-- @generated
WARNING: This section is auto-generated. Do not edit directly.
Changes will be overwritten when documentation is regenerated.
Run 'just gen-readme' to regenerate. -->
- [Public Preview Note](#public-preview-note)
- [Disclaimer](#disclaimer)
- [Getting Started](#getting-started)
- [Getting Started Examples](#getting-started-examples)
- [Examples](#examples)
- [Cluster Topology Configuration](#cluster-topology-configuration)
- [Requirements](#requirements)
- [Providers](#providers)
- [Resources](#resources)
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

This section guides you through the basic steps to set up Terraform and run this module to create a new [development cluster](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.2.0/examples/08_development_cluster) as a practical example.

### Pre Requirements

**NOTE**: If you are familiar with Terraform and already have a project configured in MongoDB Atlas, go to [Create a New Cluster](#create-a-new-cluster)

Perform the following steps to download and configure the tools required to create a new MongoDB Atlas development cluster:

1. Install [Terraform](https://developer.hashicorp.com/terraform/install).

2. [Sign in](https://account.mongodb.com/account/login) or [create](https://account.mongodb.com/account/register) your MongoDB Atlas Account.

3. Configure your [authentication](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs#authentication) method.

   **NOTE**: Service Accounts (SA) is the preferred authentication method. See [Grant Programatic Access to an Organization](https://www.mongodb.com/docs/atlas/configure-api-access/#grant-programmatic-access-to-an-organization) in the MongoDB Atlas documentation for detailed instructions on configuring SA access to your project.

4. Use an existing [MongoDB Atlas Project](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs/resources/project) or [create a new Atlas Project](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.2.0/examples/08_development_cluster/README.md/#optionally-create-a-new-atlas-project-resource).

### Create a New Cluster

Perform the following steps to create a new cluster using the cluster module:

1. Create your Terraform configuration files.
  Ensure your files contain the code provided in this repository:
  
   - [main.tf](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.2.0/examples/08_development_cluster/README.md/#code-snippet)
   - [variables.tf](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.2.0/examples/08_development_cluster/variables.tf)
   - [versions.tf](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.2.0/examples/08_development_cluster/versions.tf)

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
<!-- @generated
WARNING: This section is auto-generated. Do not edit directly.
Changes will be overwritten when documentation is regenerated.
Run 'just gen-readme' to regenerate. -->
## Getting Started Examples

Cluster Type | Environment | Name
--- | --- | ---
REPLICASET | Development | [Development Cluster](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.2.0/examples/08_development_cluster)
SHARDED | Production | [Production Cluster with Auto Scaling](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.2.0/examples/01_production_cluster_with_auto_scaling)
SHARDED | Production | [Production Cluster with Manual Scaling](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.2.0/examples/02_production_cluster_with_manual_scaling)

## Examples

Cluster Type | Name
--- | ---
SHARDED | [Cluster with Analytics Nodes](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.2.0/examples/03_cluster_with_analytics_nodes)
REPLICASET | [Cluster with Multi Regions Local (US_EAST_1 + US_EAST_2)](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.2.0/examples/04_cluster_with_multi_regions_local)
SHARDED | [Cluster with Multi Regions Global (US+EU)](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.2.0/examples/05_cluster_with_multi_regions_global)
GEOSHARDED | [Cluster with Multi Zones (GEOSHARDED)](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.2.0/examples/06_cluster_with_multi_zones)
SHARDED | [Cluster with Multi Clouds (AWS+AZURE)](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.2.0/examples/07_cluster_with_multi_clouds)
SHARDED | [Cluster using the `replication_specs` to define Cluster Topology](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.2.0/examples/09_cluster_using_replication_specs)
GEOSHARDED | [Cluster with Multi Zone and each zone with multiple shards (Advanced)](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.2.0/examples/10_cluster_with_multi_zone_multi_shards)
Multiple | [Demonstrate how to create a module "on-top" of the module with a simplified interface (cluster_size=S/M/L)](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.2.0/examples/11_module_wrapper_cluster_size)
SHARDED | [Cluster with uniform SHARDED topology using `shard_count`](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.2.0/examples/12_cluster_uniform_sharded_topology)

<!-- END_TABLES -->

## Cluster Topology Configuration

**For a comprehensive guide on cluster topology configuration, see [Cluster Topology Guide](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.2.0/docs/cluster_topology.md), which includes detailed explanations, examples, and migration instructions.**

This module offers two mutually exclusive ways to configure cluster topology:

- [Option 1 - `regions` Variables](#cluster-topology-option-1---regions-variables)
- [Option 2 - `replication_specs` Variables](#cluster-topology-option-2---replication_specs-variables)

<!-- BEGIN_TF_DOCS -->
<!-- @generated
WARNING: This section is auto-generated by terraform-docs. Do not edit directly.
Changes will be overwritten when documentation is regenerated.
Run 'just docs' to regenerate.
-->
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
<!-- @generated
WARNING: This grouped inputs section is auto-generated. Do not edit directly.
Changes will be overwritten when documentation is regenerated.
Run 'just docs' to regenerate.
-->
## Required Variables

### project_id

Unique 24-hexadecimal digit string that identifies your project, for example `664619d870c247237f4b86a6`. It is found listing projects in the Admin API or selecting a project in the UI and copying the path in the URL.

**NOTE**: Groups and projects are synonymous terms. Your group id is the same as your project id. For existing groups, your group/project id remains the same. The resource and corresponding endpoints use the term groups.

Type: `string`

### name

Human-readable label that identifies this cluster, for example: `my-product-cluster`.

Type: `string`

### cluster_type

Type of the cluster that you want to create. Valid values are `REPLICASET` / `SHARDED` / `GEOSHARDED`.

Type: `string`


## Cluster Topology Option 1 - `regions` Variables

This option is mutually exclusive with the `replication_specs` variable options and requires setting `replication_specs = []`.
See also [why two options?](#why-two-options-for-cluster-topology).

### regions

The simplest way to define your cluster topology:
- Set `name`, for example `US_EAST_1`, see all valid [region names](https://www.mongodb.com/docs/atlas/cloud-providers-regions/).
- Set `node_count`, `node_count_read_only`, `node_count_analytics` depending on your needs.
- Set `provider_name` (AWS/AZURE/GCP) or use the "root" level `provider_name` variable if all regions share the `provider_name`.
- For `cluster_type.REPLICASET`: omit both `shard_number` and `zone_name`.
- For `cluster_type.SHARDED`: set `shard_number` on each region or use the `shard_count` [variable](#shard_count); do not set `zone_name`. Regions with the same `shard_number` belong to the same shard.
- For `cluster_type.GEOSHARDED`: set `zone_name` on each region; optionally set `shard_number`. Regions with the same `zone_name` form one zone.
- See [auto_scaling](#auto-scaling) vs [manual scaling](#manual-scaling) below.

**NOTE**:
- The order in which region blocks are defined in this list determines their priority within each shard or zone.
  - The first region gets priority 7 (maximum), the next 6, and so on (minimum 0). For more context, see [this section of the Atlas Admin API documentation](https://www.mongodb.com/docs/api/doc/atlas-admin-api-v2/operation/operation-creategroupcluster#operation-creategroupcluster-body-application-vnd-atlas-2024-10-23-json-replicationspecs-regionconfigs-priority).
- Within a zone, `shard_numbers` are specific to that zone and independent of the `shard_number` in any other zones.
- The `shard_number` variable is specific to this module. It groups regions within a shard and does not represent an actual value in Atlas.

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

### provider_name

AWS/AZURE/GCP. The value of this variable is set on the root level. It is contained inside of each `region`.

Type: `string`

Default: `null`

### shard_count

Number of shards for SHARDED clusters.

- When set, all shards share the same region topology (each shard gets the same regions list).
- Do NOT set `regions[*].shard_number` when `shard_count` is set (they are mutually exclusive).
- When unset, you must set `regions[*].shard_number` on every region to explicitly group regions into shards.

Type: `number`

Default: `null`


### Auto Scaling

#### auto_scaling

Auto scaling config for electable/read-only specs. Enabled by default with Architecture Center recommended defaults.

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

#### auto_scaling_analytics

Auto scaling config for analytics specs.

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


### Manual Scaling

#### instance_size

Default `instance_size` in electable/read-only specs. Only used when `auto_scaling.compute_enabled = false`. Defaults to `M10` if not specified.

Type: `string`

Default: `null`

#### instance_size_analytics

Default `instance_size` in analytics specs. Do **not** set if using `auto_scaling_analytics`.

Type: `string`

Default: `null`

#### disk_size_gb

Storage capacity of instance data volumes expressed in gigabytes. Increase this number to add capacity.

Consider the following

- This value must be equal for all shards and node types.
- This value is not configurable on M0/M2/M5 clusters.
- If you specify a disk size below the minimum (10 GB), this parameter defaults to the minimum disk size value.
- Storage charge calculations depend on whether you choose the default value or a custom value.
- The maximum value for disk storage cannot exceed 50 times the maximum RAM for the selected cluster. If you require more storage space, consider upgrading your cluster to a higher tier.

Type: `number`

Default: `null`

#### disk_iops

Only valid for AWS and Azure instances.

##### AWS
Target IOPS (Input/Output Operations Per Second) desired for storage attached to this hardware.

Change this parameter if you:

- set `"replication_specs[n].region_configs[m].provider_name" to "AWS"`.
- set `"replication_specs[n].region_configs[m].electable_specs.instance_size" to "M30"` or greater (not including `Mxx_NVME` tiers).

- set `"replication_specs[n].region_configs[m].electable_specs.ebs_volume_type" to "PROVISIONED"`.

The maximum input/output operations per second (IOPS) depend on the selected `instance_size` and `disk_size_gb`.
This parameter defaults to the cluster tier's standard IOPS value.
Changing this value impacts cluster cost.
MongoDB Cloud enforces minimum ratios of storage capacity to system memory for given cluster tiers. This keeps cluster performance consistent with large datasets.

- Instance sizes `M10` to `M40` have a ratio of disk capacity to system memory of 60:1.
- Instance sizes greater than `M40` have a ratio of 120:1.

##### Azure
Target throughput desired for storage attached to your Azure-provisioned cluster. Change this parameter if you:

- set `"replication_specs[n].region_configs[m].provider_name" : "Azure"`.
- set `"replication_specs[n].region_configs[m].electable_specs.instance_size" : "M40"` or greater not including `Mxx_NVME` tiers.

The maximum input/output operations per second (IOPS) depend on the selected `instance_size` and `disk_size_gb`.
This parameter defaults to the cluster tier's standard IOPS value.
Changing this value impacts cluster cost.

Type: `number`

Default: `null`

#### ebs_volume_type

Type of storage you want to attach to your AWS-provisioned cluster.\n\n- `STANDARD` volume types can't exceed the default input/output operations per second (IOPS) rate for the selected volume size. \n\n- `PROVISIONED` volume types must fall within the allowable IOPS range for the selected volume size. You must set this value to (`PROVISIONED`) for NVMe clusters.

Type: `string`

Default: `null`


## Cluster Topology Option 2 - `replication_specs` Variables

This option is mutually exclusive with the `regions` variable options and requires setting `regions = []`.
See also [why two options?](#why-two-options-for-cluster-topology).

### replication_specs

List of settings that configure your cluster regions. This array has one object per shard representing node configurations in each shard. For replica sets there is only one object representing node configurations.

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


## Production Recommendations (Enabled By Default)

These recommendations are based on the [Atlas Architecture Center Documentation](https://www.mongodb.com/docs/atlas/architecture/current/hierarchy/#atlas-cluster-size-guide)

### advanced_configuration

Additional settings for an Atlas cluster.

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

### backup_enabled

Recommended for production clusters. Flag that indicates whether the cluster can perform backups. If set to `true`, the cluster can perform backups; if set to `false`, the cluster doesn't use backups. You must set this value to `true` for NVMe clusters. Backup uses [Cloud Backups](https://docs.atlas.mongodb.com/backup/cloud-backup/overview/) for dedicated clusters and [Shared Cluster Backups](https://docs.atlas.mongodb.com/backup/shared-tier/overview/) for tenant clusters.

Type: `bool`

Default: `true`

### pit_enabled

Recommended for production clusters. Flag that indicates whether the cluster uses continuous cloud backups.

Type: `bool`

Default: `true`

### retain_backups_enabled

Recommended for production clusters. Flag that indicates whether to retain backup snapshots for the deleted dedicated cluster.

Type: `bool`

Default: `true`


## Production Recommendations (Manually Configured)

These recommendations are based on the [Atlas Architecture Center Documentation](https://www.mongodb.com/docs/atlas/architecture/current/hierarchy/#atlas-cluster-size-guide)

### encryption_at_rest_provider

Cloud service provider that manages your customer keys to provide an additional layer of encryption at rest for the cluster. To enable customer key management for encryption at rest, the cluster **replication_specs[n].region_configs[m].{type}_specs.instance_size** setting must be `M10` or higher.

Type: `string`

Default: `null`

### redact_client_log_data

Enable or disable log redaction.

This setting configures the `mongod` or `mongos` to redact any document field contents from a message accompanying a given log event before logging. This prevents the program from writing potentially sensitive data stored on the database to the diagnostic log. Metadata such as error or operation codes, line numbers, and source file names are still visible in the logs.

Use `redact_client_log_data` in conjunction with Encryption at Rest and TLS/SSL (Transport Encryption) to assist compliance with regulatory requirements.

*Note*: Changing this setting on a cluster will trigger a rolling restart as soon as the cluster is updated.

Type: `bool`

Default: `true`

### tags

Map that contains key-value pairs between 1 to 255 characters in length for tagging and categorizing the cluster.
We recommend setting the following values:
- Department
- Team name
- Application name
- Environment
- Version
- Email contact
- Criticality

These values can be used for:
- Billing.
- Data classification.
- Regional compliance requirements for audit and governance purposes.

Type: `map(string)`

Default: `{}`

### termination_protection_enabled

Recommended for production clusters. Flag that indicates whether termination protection is enabled on the cluster. If set to `true`, MongoDB Cloud does not delete the cluster; if set to `false`, MongoDB Cloud deletes the cluster.

Type: `bool`

Default: `null`


## Optional Variables

### accept_data_risks_and_force_replica_set_reconfig

If reconfiguration is necessary to regain a primary due to a regional outage, submit this field alongside your topology reconfiguration to request a new regional outage resistant topology.

Forced reconfigurations during an outage of the majority of electable nodes carry a risk of data loss if replicated writes (even majority committed writes) have not been replicated to the new primary node. See [Replication](https://www.mongodb.com/docs/manual/replication/) in the MongoDB Atlas documentation for more information. To proceed with an operation which carries that risk, set `accept_data_risks_and_force_replica_set_reconfig` to the current date.

Type: `string`

Default: `null`

### bi_connector_config

Setting needed to configure the MongoDB Connector for Business Intelligence for this cluster.

Type:

```hcl
object({
  enabled         = optional(bool)
  read_preference = optional(string)
})
```

Default: `null`

### config_server_management_mode

Config Server Management Mode for creating or updating a sharded cluster.

When configured as `ATLAS_MANAGED`, Atlas may automatically switch the cluster's config server type for optimal performance and savings.

When configured as `FIXED_TO_DEDICATED`, the cluster always uses a dedicated config server.

Type: `string`

Default: `null`

### delete_on_create_timeout

Flag that indicates whether to delete the cluster if the cluster creation times out. Default is false.

Type: `bool`

Default: `null`

### global_cluster_self_managed_sharding

Set this field to configure the Sharding Management Mode when creating a new Global Cluster.

When set to false, the management mode is set to Atlas-Managed Sharding. This mode fully manages the sharding of your Global Cluster and is built to provide a seamless deployment experience.

When set to true, the management mode is set to Self-Managed Sharding. This mode leaves the management of shards in your hands and is built to provide an advanced and flexible deployment experience.

*Important*: This setting cannot be changed once the cluster is deployed.

Type: `bool`

Default: `null`

### mongo_db_major_version

MongoDB major version of the cluster.

On creation: Choose from the available versions of MongoDB, or leave unspecified for the current recommended default in the MongoDB Cloud platform. The recommended version is a recent Long Term Support version. The default is not guaranteed to be the most recently released version throughout the entire release cycle. For versions available in a specific project, see the linked documentation or use the API endpoint for [project LTS versions endpoint](#tag/Projects/operation/getProjectLTSVersions).

 On update: Increase version only by one major version at a time. If the cluster is pinned to a MongoDB feature compatibility version exactly one major version below the current MongoDB version, you can downgrade to the previous MongoDB major version.

Type: `string`

Default: `null`

### paused

Flag that indicates whether the cluster is paused.

Type: `bool`

Default: `null`

### pinned_fcv

Pins the Feature Compatibility Version (FCV) to the current MongoDB version with a provided expiration date. To unpin the FCV, the `pinned_fcv` attribute must be removed. This operation can take several minutes as the request processes through the MongoDB data plane. Once FCV is unpinned it will not be possible to downgrade the `mongo_db_major_version`. We recommend updating to `pinned_fcv` in isolation from other cluster changes. If a plan contains multiple changes, the FCV change will be applied first. If FCV is unpinned past the expiration date the `pinned_fcv` attribute must be removed. See the following [knowledge hub article](https://kb.corp.mongodb.com/article/000021785/) and the [FCV documentation](https://www.mongodb.com/docs/atlas/tutorial/major-version-change/#manage-feature-compatibility--fcv--during-upgrades) for more details.

Type:

```hcl
object({
  expiration_date = string
})
```

Default: `null`

### replica_set_scaling_strategy

Set this field to configure the replica set scaling mode for your cluster.

By default, Atlas scales under `WORKLOAD_TYPE`. This mode allows Atlas to scale your analytics nodes in parallel to your operational nodes.

When configured as `SEQUENTIAL`, Atlas scales all nodes sequentially. This mode is intended for steady-state workloads and applications performing latency-sensitive secondary reads.

Type: `string`

Default: `null`

### root_cert_type

Root Certificate Authority that MongoDB Cloud cluster uses. MongoDB Cloud supports Internet Security Research Group.

Type: `string`

Default: `null`

### timeouts

Timeouts for `create`, `update`, and `delete` operations.

Type:

```hcl
object({
  create = optional(string)
  delete = optional(string)
  update = optional(string)
})
```

Default: `null`

### version_release_system

Method by which the cluster maintains the MongoDB versions. If value is `CONTINUOUS`, you must not specify `mongo_db_major_version*`.

Type: `string`

Default: `null`

<!-- END_TF_INPUTS_RAW -->

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

📖 **For detailed guidance on when to use each approach, see the [Cluster Topology Guide](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.2.0/docs/cluster_topology.md)**

### Why does this module require Terraform 1.9+ when the provider supports 1.7.x+?

This module requires Terraform 1.9+ due to the use of cross-variable validation references, which are only supported in Terraform 1.9 and later. While the [MongoDB Atlas Provider](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs#hashicorp-terraform-version-compatibility-matrix) supports Terraform 1.7.x+, this module's validation patterns require 1.9+.

See [Terraform Version Requirements](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.2.0/docs/terraform_version_requirements.md) for detailed explanation.

### What is the `provider_meta "mongodbatlas"` doing?

- This block allows us to track the usage of this module by updating the User-Agent of requests to Atlas, for example:
  - `User-Agent: terraform-provider-mongodbatlas/2.1.0 Terraform/1.13.1 module_name/cluster module_version/0.1.0`
- Note: We **do not** send any configuration-specific values, only these values to help us track feature adoption.
- You can use `export TF_LOG=debug` to see the API requests with headers and their responses.
