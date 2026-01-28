# Contributing to terraform-mongodbatlas-cluster

Quick guide for contributing to this Terraform module.

## Quick Start

```bash
# Install required tools (macOS with Homebrew)
brew install just terraform tflint terraform-docs uv pre-commit

# Or use mise for automated tool management
mise install

# Clone and setup
git clone <repo-url>
cd terraform-mongodbatlas-cluster

# Install git hooks (optional but recommended)
pre-commit install
pre-commit install --hook-type pre-push

# Verify installation
just

# Before committing (runs automatically if hooks installed)
just pre-commit
```

**Tools**: [just](https://just.systems/) • [Terraform](https://www.terraform.io/) • [TFLint](https://github.com/terraform-linters/tflint) • [terraform-docs](https://terraform-docs.io/) • [uv](https://docs.astral.sh/uv/) • [pre-commit](https://pre-commit.com/) • [mise](https://mise.jdx.dev/) (for version compatibility testing)

## Prerequisites

- macOS with [Homebrew](https://brew.sh/) or Linux
- [Git](https://git-scm.com/) for version control
- [uv](https://docs.astral.sh/uv/) Python installer (for doc generation)
- [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) Account (for testing, optional)

## Development Workflow

```bash
# Daily workflow
just fmt                      # Format Terraform code
just lint                     # Run Terraform linters
just py-fmt                   # Format Python code
just py-check                 # Lint Python code
just py-test                  # Run Python unit tests
just pre-commit               # Run fast checks (fmt, validate, lint, check-docs, py-check)
just pre-push                 # Run slower checks (pre-commit + unit-plan-tests, py-test)

# Documentation
just docs                     # Generate all docs
just check-docs               # Verify docs are up-to-date (CI mode)

# Terraform file generation
just tf-gen --config gen.yaml     # Generate all targets from config
just tf-gen --config gen.yaml --dry-run  # Preview without writing

# Testing (see test-guide.md for full details)
just unit-plan-tests          # Plan-only tests (no credentials)
just dev-integration-test     # Single apply test (requires credentials)
just test-compat              # Terraform version compatibility

# Release (maintainers)
just check-release-ready v1.0.0  # Validate prerequisites
just release-commit v1.0.0       # Create commits and tag
just release-post-push           # Revert after pushing tag
```

Run `just --list` for all commands.

## Git Hooks

Git hooks automate checks before commits and pushes. Install with [pre-commit](https://pre-commit.com/):

```bash
pre-commit install                    # Install pre-commit hook
pre-commit install --hook-type pre-push  # Install pre-push hook
```

| Hook | Runs | Command |
|------|------|---------|
| pre-commit | Before each commit | `just pre-commit` (fmt, validate, lint, docs, py-check) |
| pre-push | Before each push | `just pre-push` (pre-commit + unit-plan-tests, py-test) |

To skip hooks temporarily: `git commit --no-verify` or `git push --no-verify`.

## CI/CD Workflows

### Workflow Summary

| Workflow | Triggers | Just Targets | Provider |
|----------|----------|--------------|----------|
| `code-health.yml` | PR, push main, nightly | `pre-commit`, `unit-plan-tests`, `test-compat`, `plan-snapshot-test` | master |
| `dev-integration-test.yml` | PR/push (tf changes), nightly | `dev-integration-test` | master |
| `pre-release-tests.yml` | manual | `tftest-all`, `apply-examples`, `destroy-examples` | registry (or custom branch) |
| `release.yml` | manual | `check-release-ready`, `release-commit`, `generate-release-body` | N/A |

### Provider Testing Policy

- **PR/push/nightly**: Uses provider `master` branch via `TF_CLI_CONFIG` dev_overrides
- **Pre-release**: Uses latest published registry provider by default; optionally specify `provider_branch` input to test with a specific provider branch

### Required Secrets

| Secret | Description |
|--------|-------------|
| `MONGODB_ATLAS_ORG_ID` | Atlas organization ID for tests |
| `MONGODB_ATLAS_CLIENT_ID` | Service account client ID |
| `MONGODB_ATLAS_CLIENT_SECRET` | Service account client secret |
| `MONGODB_ATLAS_BASE_URL` | Atlas API base URL (cloud-dev) |

### Required Variables

| Variable | Description |
|----------|-------------|
| `MONGODB_ATLAS_PROJECT_ID_SNAPSHOT_TEST` | Project ID for plan snapshot tests |

## Testing

See [test-guide.md](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.3.0/contributing/test-guide.md) for detailed testing documentation including:
- Authentication setup
- Unit and integration tests
- Version compatibility testing
- Plan snapshot tests with workspace tooling

## Variable Validation Patterns

When adding or modifying variable validations, follow these patterns:

### Handling Null Values with `try()`

When validating numeric values that might be `null`, wrap `floor()` comparisons with `try()` to handle null values gracefully:

```hcl
validation {
  condition = var.value == null || try(var.value == floor(var.value) && var.value >= 0, false)
  error_message = "value must be a non-negative integer if provided."
}
```

**Why?** In Terraform 1.9-1.11, short-circuit evaluation behavior changed. The `try()` function ensures that if `floor()` receives a `null` value, it returns `false` instead of causing an error, allowing the validation to pass when the value is `null` (first clause will be `true`).

### Cross-Variable Validation References

This module uses cross-variable validation references (requires Terraform 1.9+):

```hcl
variable "shard_count" {
  validation {
    condition     = var.shard_count == null || var.cluster_type == "SHARDED"
    error_message = "shard_count can only be set when cluster_type is SHARDED."
  }
}
```

**Note**: Cross-variable validation references are a key reason this module requires Terraform >= 1.9. See [Terraform Version Requirements](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.3.0/contributing/docs/terraform_version_requirements.md) for details.

## Documentation

Documentation is auto-generated from Terraform source files and configuration. Run `just docs` before committing to regenerate all docs and verify they are up-to-date.

### Documentation Generation Workflow

The `just docs` command runs the following steps in order:

1. Format Terraform files (`terraform fmt`)
2. Generate terraform-docs sections (Requirements, Providers, Resources, Variables, Outputs)
3. Generate grouped Inputs section from `variable_*.tf` files (organizes variables into logical categories like "Required", "Auto Scaling", etc.)
4. Generate root README.md TOC and example tables
5. Generate example README.md and versions.tf files

### Generated Files and Sections

Do not edit these files or sections directly. They are regenerated automatically:

- **Root README.md**:
  - Table of Contents (`<!-- BEGIN_TOC -->` to `<!-- END_TOC -->`)
  - Example tables (`<!-- BEGIN_TABLES -->` to `<!-- END_TABLES -->`)
  - Requirements, Providers, Resources sections (`<!-- BEGIN_TF_DOCS -->` to `<!-- END_TF_DOCS -->`)
  - Grouped Inputs section (between terraform-docs markers)
  - Outputs section (within `<!-- BEGIN_TF_DOCS -->` markers)
- **Example README.md files** (`examples/*/README.md`): Entire files are generated from templates

### Regenerating Documentation Locally

```bash
# Regenerate all documentation
just docs

# Verify documentation is up-to-date (for CI/pre-push)
just check-docs
```

If `just check-docs` fails, it means documentation is out of sync. Run `just docs` locally and commit the changes.

### Fixing CI Documentation Failures

When CI fails with "Documentation is out of date":

1. Run `just docs` locally
2. Review the generated changes with `git diff`
3. Commit the changes if they are expected
4. If changes are unexpected, check:
   - Did you modify `variable_*.tf` files? Update variable descriptions there.
   - Did you modify `.terraform-docs.yml`? Ensure configuration is correct.
   - Did you add a new example? Add it to `docs/examples.yaml` tables configuration.

### Adding New Examples

1. Create folder: `NN_descriptive_name`
2. Add to `docs/examples.yaml` tables configuration:
   ```yaml
   - folder: NN
     name: Descriptive Name
     title_suffix: (Optional)  # e.g., "(AWS + Azure)"
   ```
3. Run `just docs` to generate the example README.md

### Documentation Scripts

Scripts are organized in `.github/` subdirectories ([Python](https://www.python.org/) 3.14+, managed via `pyproject.toml`):

**docs/** - Documentation generation:
- `root_readme.py` - Generates root README TOC and tables
- `examples_readme.py` - Generates example README.md files
- `submodule_readme.py` - Transforms submodule README source paths to registry source
- `generate_inputs_from_readme.py` - Generates grouped Inputs section from terraform-docs output
- `md_link_absolute.py` - Converts relative links to absolute GitHub URLs for releases

**release/** - Release and versioning:
- `tf_registry_source.py` - Computes Terraform Registry source from git remote
- `release_notes.py` - Generates release notes from GitHub commits
- `update_version.py` - Updates module version in versions.tf
- `validate_version.py` - Validates version format for releases

**changelog/** - Changelog management:
- `build_changelog.py` - Generates CHANGELOG.md from `.changelog/*.txt` entries
- `update_changelog_version.py` - Updates CHANGELOG.md version header with current date
- `generate_release_body.py` - Generates GitHub release body from CHANGELOG.md

**workspace/** - Plan snapshot testing:
- `gen.py`, `plan.py`, `reg.py`, `run.py` - Workspace test orchestration

**dev/** - Development utilities:
- `dev_vars.py` - Generates dev.tfvars for local testing
- `test_compat.py` - Terraform CLI version compatibility testing

**Testing**: Python unit tests use [pytest](https://pytest.org/). Run `just py-test` to execute all tests in `*_test.py` files (excludes `test_compat.py`).

**tf_gen/** - Terraform file generation:
- `cli.py` - CLI entry point for `just tf-gen`
- `config.py` - Configuration models (GenerationTarget, ProviderGenConfig)
- `generators/` - File generators (variables_tf.py, main_tf.py, outputs_tf.py)
- `schema/` - Provider schema parsing

See [tf-gen README](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.3.0/.github/tf_gen/README.md) for configuration reference and examples.

See [documentation-guide.md](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.3.0/contributing/documentation-guide.md) for detailed documentation contributor guidelines.

## Release Process (Maintainers)

Releases are automated via the `release.yml` GitHub Actions workflow. The workflow uses a 2-commit + revert strategy to keep tags reachable from main branch history.

### Version Placeholder

During development, `module_version` in `versions.tf` is set to `"local"` as a placeholder. This indicates you're working with a development version and helps distinguish it from released versions. The release process automatically replaces `"local"` with the actual version number.

### Creating a Release (GitHub Actions)

Trigger the `Release` workflow from GitHub Actions with the version (e.g., `v1.0.0`).

**What happens**:
1. Pre-release validation (version format, changelog, docs)
2. Changelog commit: Updates `CHANGELOG.md` with version header (stays on main)
3. Release commit: Updates `module_version`, regenerates docs with absolute links, registry source URLs
4. Tag created on release commit
5. Tag pushed to origin
6. Release commit reverted on main (restores `"local"` version and relative links)
7. GitHub release created with changelog content

**Result on main after release**:
```
main: ──[changelog: v1.0.0]──[release: v1.0.0]──[revert release]──
                                    │
                              tag: v1.0.0
```

### Manual Release (Local)

```bash
just check-release-ready v1.0.0   # Validate prerequisites
just release-commit v1.0.0        # Create changelog + release commits, tag
git push origin v1.0.0            # Push tag
just release-post-push            # Revert release commit
git push origin main              # Push main with changelog + revert
```

**Why 2-commit + revert?**
- Tags are reachable from main (required for `git describe`, bisect)
- Tagged commit has correct version-specific values (registry URLs, `module_version`)
- Main stays in development state (`"local"` version, relative links)

## Submitting Changes

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and verify
just pre-commit
just plan-examples YOUR_PROJECT_ID  # if applicable

# Commit and push
git add .
git commit -m "feat: your feature description"
git push origin feature/your-feature-name
```

## Getting Help

- Check [Issues](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.3.0/../../../issues) for similar problems
- Create new issue with output from `just pre-commit` if needed
- See [Terraform docs](https://www.terraform.io/docs) and [MongoDB Atlas Provider docs](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs)
