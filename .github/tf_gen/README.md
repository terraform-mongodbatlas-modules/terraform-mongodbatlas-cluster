# tf-gen: Terraform File Generator

Generate `variables.tf`, `main.tf`, and `outputs.tf` from Terraform provider schemas.

## Prerequisites

- [Python](https://www.python.org/) 3.14+
- [uv](https://docs.astral.sh/uv/) for dependency management
- [Terraform](https://www.terraform.io/) 1.9+

## Quick Start

1. Create a `gen.yaml` configuration file:

```yaml
providers:
  - provider_name: mongodbatlas
    resources:
      project:
        - output_dir: .
          label: this
```

2. Run the generator:

```bash
just tf-gen --config gen.yaml
```

## CLI Usage

```
Usage: python -m tf_gen [OPTIONS]

Generate Terraform files from provider schemas.

Options:
  -c, --config PATH        Path to gen.yaml [required]
  -t, --target TEXT       Filter by resource type (repeatable)
  -d, --dest-path PATH    Base directory for output [default: cwd]
  --cache-dir PATH        Directory to cache provider schemas
  --dry-run               Print without writing
  --help                  Show this message and exit.
```

**Examples:**

```bash
# Generate all targets from config
just tf-gen --config gen.yaml

# Generate specific resource type
just tf-gen --config gen.yaml --target project

# Preview without writing
just tf-gen --config gen.yaml --dry-run

# Cache schemas for faster runs
just tf-gen --config gen.yaml --cache-dir .tf-gen-cache
```

## Configuration Reference

### Provider Configuration

```yaml
providers:
  - provider_name: mongodbatlas           # Provider name (required)
    provider_source: mongodb/mongodbatlas # Provider source (auto-resolved)
    provider_version: "~> 1.0"            # Version constraint
    resources:
      project:                            # Resource type (without provider prefix)
        - output_dir: .
          # ... target options
```

### Generation Target Options

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `output_dir` | Path | `cwd()` | Directory for generated files |
| `label` | str | `"this"` | Terraform resource label |
| `files` | list | `[variable, resource, output]` | Which files to generate |

**File Skipping:**

```yaml
# Default: generate all 3 files
files: [variable, resource, output]

# Skip resource file (outputs-only targets)
files: [variable, output]

# Skip variables (when using single variable from parent)
files: [resource, output]
```

**Filename Overrides:**

| Field | Default |
|-------|---------|
| `variable_filename` | `variables_resource.tf` |
| `resource_filename` | `main.tf` |
| `output_filename` | `outputs.tf` |

**Path Resolution:**

```
Final path = --dest-path (CLI) + output_dir (config)

Example:
  CLI: just tf-gen --config gen.yaml --dest-path /code/aws-module
  Config: output_dir: ./modules/privatelink
  Result: /code/aws-module/modules/privatelink/
```

## File Types

### variables.tf Generation

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `variables_prefix` | str | `""` | Prefix for variable names |
| `variables_excluded` | list[str] | `[]` | Attributes to skip |
| `variables_required` | list[str] | `[]` | Force attributes to be required |
| `all_variables_optional` | bool | `false` | Make all variables optional with `default = null` |
| `use_single_variable` | bool | `false` | Generate single object variable instead of individual variables |
| `variable_tf` | dict | `{}` | Per-variable overrides |

**Variable Overrides (`variable_tf`):**

```yaml
variable_tf:
  project_id:
    description: "Custom description"
  cluster_type:
    default: "REPLICASET"
    sensitive: true
  provider_name:
    validation:
      condition: 'var.provider_name == null || contains(["AWS", "AZURE", "GCP"], var.provider_name)'
      error_message: "Only AWS/AZURE/GCP are allowed."
```

Available override fields: `name`, `description`, `type`, `default`, `sensitive`, `validation`

**Generation Modes:**

| Mode | Config | Variable Pattern | Resource Reference |
|------|--------|------------------|-------------------|
| Expanded | `use_single_variable: false` | `variable "name" { type = string }` | `var.name` |
| Single | `use_single_variable: true` | `variable "mongodbatlas_project" { type = object({...}) }` | `var.mongodbatlas_project.name` |

### main.tf Generation

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `resource_tf` | ResourceMetaArgs | `{}` | Meta-arguments (count, provider, depends_on, lifecycle) |
| `resource_tf_var_overrides` | dict | `{}` | Override variable references in resource block |

**Resource Meta-Arguments (`resource_tf`):**

```yaml
resource_tf:
  count: "local.needs_resource ? 1 : 0"
  provider: "aws.west"
  depends_on: ["aws_vpc.main"]
  lifecycle: |
    ignore_changes = [tags]
```

### outputs.tf Generation

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `outputs_prefix` | str | `""` | Prefix for output names |
| `outputs_excluded` | list[str] | `[]` | Computed attributes to skip |
| `output_tf_overrides` | dict | `{}` | Per-output overrides |
| `use_single_output` | bool | `false` | Generate single object output |
| `use_resource_count` | bool | `false` | Use `length()` guards for conditional resources |
| `include_id_field` | bool | `false` | Include `id` in outputs |
| `output_attribute_max_children` | int | `5` | Max nested children to expand |

**Output Overrides (`output_tf_overrides`):**

```yaml
output_tf_overrides:
  connection_strings:
    description: "Connection strings for all nodes"
    sensitive: true
    include_children: true
```

Available override fields: `name`, `value`, `include_children`, `sensitive`

**Generation Modes:**

| Mode | Config | Use Case |
|------|--------|----------|
| Expanded | `use_single_output: false` | Individual outputs per computed attribute (default) |
| Single | `use_single_output: true` | Single output object with top-level computed attributes |
| Count-safe | `use_resource_count: true` | Outputs use `length()` guards for conditional resources |

## Section Markers

Generated code coexists with manual code using START/END markers:

```hcl
# START Code generated by `tf-gen --config gen.yaml --target project`. DO NOT EDIT.
variable "name" {
  type = string
}
# END Code generated by `tf-gen --config gen.yaml --target project`. DO NOT EDIT.

# Manual additions below
variable "custom_field" { ... }
```

- **Append behavior:** If markers don't exist, generated content is appended
- **Update behavior:** If markers exist, content between them is replaced
- **Manual code:** Code outside markers is preserved

## Schema to TF Conversion

### Dynamic Block Patterns

The generator creates dynamic blocks based on the schema's nesting mode:

| Block Type | Nesting Mode | for_each Pattern | Variable Type |
|------------|--------------|------------------|---------------|
| Optional list/set | list, set | `var.field == null ? [] : var.field` | `list/set(object({...}))` |
| Optional single | single, max_items=1 | `var.field == null ? [] : [var.field]` | `object({...})` |
| Required single | single, max_items=1 | Direct block (no dynamic) | `object({...})` |

**Key simplification:** When a block has `max_items: 1`, the variable is generated as a single `object({...})` instead of `list(object({...}))`.

### Variable Type Inference

- **Required attributes:** No `nullable`, no `default`
- **Optional attributes:** `nullable = true`, `default = null`
- **Schema type mapping:** Provider types map to Terraform types (`string`, `number`, `bool`, `list`, `set`, `map`, `object`)

## Caching

The `--cache-dir` option caches provider schema JSON files:

```bash
just tf-gen --config gen.yaml --cache-dir .tf-gen-cache
```

- **Cache key:** `{provider_source}_{provider_version}`
- **When to clear:** After changing provider version constraints
- **Default:** No caching (fetches schema each run)

## Examples

### Basic: Single Resource with Overrides

From `testdata/cli_regression/project/gen.yaml`:

```yaml
providers:
  - provider_name: mongodbatlas
    resources:
      project:
        - output_dir: .
          label: this
          variables_excluded: [teams]
          variable_tf:
            name:
              description: "Name of the MongoDB Atlas project"
            org_id:
              description: "MongoDB Atlas organization ID"
          resource_tf:
            lifecycle: |
              ignore_changes = [teams]
```

### Multi-Provider with Submodules

From `testdata/cli_regression/aws/gen.yaml`:

```yaml
providers:
  - provider_name: mongodbatlas
    resources:
      cloud_provider_access_setup:
        - output_dir: .
          label: this
          use_resource_count: true
          variables_excluded: [gcp_config, azure_config, delete_on_create_timeout, timeouts]
          outputs_excluded: [gcp_config, azure_config]
          resource_tf:
            count: "local.needs_shared_cloud_provider_access ? 1 : 0"
      cloud_provider_access_authorization:
        - output_dir: .
          label: this
          use_resource_count: true
          variables_excluded: [azure, gcp]
          outputs_excluded: [azure, gcp]
          resource_tf:
            count: "local.needs_shared_cloud_provider_access ? 1 : 0"
  - provider_name: aws
    resources:
      vpc_endpoint:
        - output_dir: ./modules/privatelink
          label: aws_endpoint
          use_resource_count: true
          variables_excluded: [timeouts, tags_all, arn, cidr_blocks, dns_entry]
          resource_tf:
            count: "var.create_vpc_endpoint ? 1 : 0"
```

## Testing

Tests are in `.github/tf_gen/` using [pytest](https://pytest.org/):

| Test File | Purpose |
|-----------|---------|
| `cli_test.py` | CLI integration and feature modes (single variable, single output, count) |
| `cli_regression_test.py` | Module config regression tests (project, aws, azure, gcp configs) |
| `schema_regression_test.py` | Per-resource schema-to-HCL generation against `testdata/regressions/` |
| `variables_tf_test.py` | Variable generation unit tests |
| `main_tf_test.py` | Resource block generation unit tests |
| `outputs_tf_test.py` | Output generation unit tests |

Run tests:

```bash
just py-test
```
