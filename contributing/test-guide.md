# Testing Guide

Guide for running tests on the terraform-mongodbatlas-cluster module.

## Authentication Setup

```bash
# Required for all tests
export MONGODB_ATLAS_CLIENT_ID=your_sa_client_id
export MONGODB_ATLAS_CLIENT_SECRET=your_sa_client_secret

# Required for integration tests (creates test project)
export MONGODB_ATLAS_ORG_ID=your_org_id

# Optional
export MONGODB_ATLAS_BASE_URL=https://cloud.mongodb.com/
```

See [MongoDB Atlas Provider Authentication](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs#authentication) for details.

## Test Commands

```bash
# Plan-only tests (no resources created)
just unit-plan-tests

# Single dev cluster test (creates resources)
just dev-integration-test

# All terraform tests (plan + apply, no filter)
just tftest-all
```

**Note**: Apply tests create temporary projects and set `termination_protection_enabled = false` for cleanup.

## Version Compatibility Testing

Test that the module validates correctly across all supported Terraform versions:

```bash
just test-compat
```

This runs `terraform init` and `terraform validate` on the root module and all examples using each version in `.terraform-versions.yaml`. Requires [mise](https://mise.jdx.dev/) for version switching.

To update the version matrix when new Terraform versions are released, edit `.terraform-versions.yaml`.

## Plan Snapshot Tests

Plan snapshot tests verify that `terraform plan` output remains consistent across changes. They use workspace directories under `tests/workspace_*/` with YAML snapshots compared via [pytest-regressions](https://pytest-regressions.readthedocs.io/).

### Workspace Commands

```bash
# Plan and compare against baselines (requires dev.tfvars with project_ids)
just ws-run -m plan-snapshot-test -v dev.tfvars

# First run or after intentional changes: create/update baselines
just ws-run -m plan-snapshot-test -v dev.tfvars --force-regen

# Plan specific examples only (e.g., 01 and 08)
just ws-run -m plan-only -e 1,8 -v dev.tfvars

# Setup project infrastructure before testing (when project_id unknown)
just ws-run -m setup-only --auto-approve

# Apply examples (creates real resources)
just ws-run -m apply -v dev.tfvars --auto-approve

# Destroy resources after testing
just ws-run -m destroy --auto-approve

# Find resources without plan_regressions entries (shows [data], [example], [module] hints)
just ws-run -m reg -u
```

### Snapshot Configuration

Add examples to `tests/workspace_cluster_examples/workspace_test_config.yaml`:

```yaml
examples:
  - number: 3                    # matches examples/03_*/
    # or name: {folder_name} instead of number
    var_groups: [shared, group1] # combine shared + group-specific vars
    plan_regressions:
      - address: module.cluster.mongodbatlas_advanced_cluster.this
        dump:
          skip_lines:
            redact_attributes: [custom_field]  # additional fields to redact
            use_default_redact: true           # include default redactions
```

Then run `just ws-run -m plan-snapshot-test -v dev.tfvars --force-regen` and commit the generated baselines.

**Snapshot organization**: Single-resource examples use flat files (`01_module_cluster_...yaml`), multi-resource examples use nested directories (`11/module_cluster_small_...yaml`).

**Sensitive value redaction**: Values are redacted as `<field_name>` instead of omitted entirely. Default redacted attributes include `secret`, `password`, `token`, `credentials`, `private_key`, `client_secret`, `tenant_id`, plus all variables from `var_groups`.

### Workspace Test Scripts

Scripts in `.github/workspace/` directory:
- `run.py` - Orchestrates workspace test runs
- `gen.py` - Generates workspace configurations
- `plan.py` - Runs terraform plan operations
- `reg.py` - Handles regression snapshot generation and comparison

## Provider Dev Branch Testing

Test against a local provider build instead of the registry version:

```bash
# Clone provider and build from source
git clone https://github.com/mongodb/terraform-provider-mongodbatlas ../provider
just setup-provider-dev ../provider

# Export the config file (printed by setup-provider-dev)
export TF_CLI_CONFIG_FILE=$(pwd)/dev.tfrc

# Now terraform commands use the local provider
just unit-plan-tests
```

CI workflows (`code-health.yml`, `dev-integration-test.yml`) automatically use the provider default branch via the `setup-provider-dev` action.
