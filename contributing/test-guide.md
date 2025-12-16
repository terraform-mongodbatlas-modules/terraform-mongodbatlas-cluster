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

# Fast integration tests - single dev cluster (creates resources)
just integration-tests
```

**Note**: Integration tests create temporary projects and set `termination_protection_enabled = false` for cleanup.

## Version Compatibility Testing

Test that the module validates correctly across all supported Terraform versions:

```bash
just test-compat
```

This runs `terraform init` and `terraform validate` on the root module and all examples using each version in `.terraform-versions.yaml`. Requires [mise](https://mise.jdx.dev/) for version switching.

To update the version matrix when new Terraform versions are released, edit `.terraform-versions.yaml`.

## Plan Snapshot Tests

Plan snapshot tests verify that `terraform plan` output remains consistent across changes. They use workspace directories under `tests/workspace_*/` with YAML snapshots compared via [pytest-regressions](https://pytest-regressions.readthedocs.io/).

### Running Snapshot Tests

```bash
# Plan and compare against baselines (requires dev.tfvars with project_ids)
just ws-run -m plan-snapshot-test -v dev.tfvars

# First run or after intentional changes: create/update baselines
just ws-run -m plan-snapshot-test -v dev.tfvars --force-regen

# Plan specific examples only (e.g., 01 and 08)
just ws-run -m plan-only -e 1,8 -v dev.tfvars
```

### Workspace Commands

```bash
# Setup project infrastructure before testing (when project_id unknown)
just ws-run -m setup-only --auto-approve

# Apply examples (creates real resources)
just ws-run -m apply -v dev.tfvars --auto-approve

# Destroy resources after testing
just ws-run -m destroy --auto-approve
```

### Adding a New Example to Snapshot Testing

1. Add entry to `tests/workspace_cluster_examples/workspace_test_config.yaml`:
   ```yaml
   examples:
     - number: 3                    # matches examples/03_*/
       var_groups: [shared, group1] # combine shared + group-specific vars
       plan_regressions:
         - address: module.cluster.mongodbatlas_advanced_cluster.this
   ```
2. Run `just ws-run -m plan-snapshot-test -v dev.tfvars --force-regen`
3. Commit baseline files in `tests/workspace_cluster_examples/plan_snapshots/`

### Workspace Test Scripts

Scripts in `.github/tf_ws/` directory:
- `run.py` - Orchestrates workspace test runs
- `gen.py` - Generates workspace configurations
- `plan.py` - Runs terraform plan operations
- `reg.py` - Handles regression snapshot comparison
