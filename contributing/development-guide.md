# Contributing to terraform-mongodbatlas-cluster

Quick guide for contributing to this Terraform module.

## Quick Start

```bash
# Install required tools (macOS with Homebrew)
brew install just terraform tflint terraform-docs uv

# Or use mise for automated tool management
mise install

# Clone and setup
git clone <repo-url>
cd terraform-mongodbatlas-cluster

# Verify installation
just

# Before committing
just check
```

**Tools**: [just](https://just.systems/) • [Terraform](https://www.terraform.io/) • [TFLint](https://github.com/terraform-linters/tflint) • [terraform-docs](https://terraform-docs.io/) • [uv](https://docs.astral.sh/uv/) • [mise](https://mise.jdx.dev/) (for version compatibility testing)

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
just check                    # Run all checks (fmt, validate, lint, check-docs, py-check, py-test)

# Documentation
just docs                     # Generate all docs
just check-docs               # Verify docs are up-to-date (CI mode)

# Testing (see test-guide.md for details)
just test                     # Run unit + integration tests
just test-compat              # Validate across all supported Terraform versions
just ws-run -m plan-snapshot-test -v dev.tfvars  # Plan snapshot tests

# Release (maintainers)
just release-commit v1.0.0    # Create release branch
just release-notes v1.0.0     # Generate release notes
just tf-registry-source       # Show Terraform Registry source
```

Run `just --list` for all commands.

## Testing

See [test-guide.md](./test-guide.md) for detailed testing documentation including:
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

**Note**: Cross-variable validation references are a key reason this module requires Terraform >= 1.9. See [Terraform Version Requirements](./docs/terraform_version_requirements.md) for details.

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

Scripts in `.github/` directory ([Python](https://www.python.org/) 3.10+):

- `root_readme.py` - Generates root README TOC and tables
- `examples_readme.py` - Generates example README.md files
- `generate_inputs_from_readme.py` - Generates grouped Inputs section from terraform-docs output
- `md_link_absolute.py` - Converts relative links to absolute GitHub URLs for releases
- `tf_registry_source.py` - Shows Terraform Registry source for the module
- `release_notes.py` - Generates release notes from GitHub commits
- `update_version.py` - Updates module version in versions.tf
- `validate_version.py` - Validates version format for releases
- `changelog/build_changelog.py` - Generates CHANGELOG.md from `.changelog/*.txt` entries
- `changelog/update_changelog_version.py` - Updates CHANGELOG.md version header with current date

**Testing**: Python unit tests use [pytest](https://pytest.org/). Run `just py-test` to execute all tests in `*_test.py` files (excludes `test_compat.py`).

See [documentation-guide.md](./documentation-guide.md) for detailed documentation contributor guidelines.

## Release Process (Maintainers)

### Version Placeholder

During development, `module_version` in `versions.tf` is set to `"local"` as a placeholder. This indicates you're working with a development version and helps distinguish it from released versions. The release process automatically replaces `"local"` with the actual version number.

### Creating a Release

```bash
# Create release branch with version-specific docs
just release-commit v1.0.0

# Review and push
git push origin v1.0.0 --tags
```

**What happens**:
1. Creates release branch `v1.0.0`
2. Updates `module_version` in `versions.tf` from `"local"` to `"v1.0.0"`
3. Regenerates all docs with absolute links
4. Commits and tags

**Why separate branches?**
- Main uses relative links (dev-friendly) and `module_version = "local"`
- Release branches use absolute links (stable docs for that version) and actual version numbers

## Submitting Changes

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and verify
just check
just plan-examples YOUR_PROJECT_ID  # if applicable

# Commit and push
git add .
git commit -m "feat: your feature description"
git push origin feature/your-feature-name
```

## Getting Help

- Check [Issues](../../../issues) for similar problems
- Create new issue with output from `just check` if needed
- See [Terraform docs](https://www.terraform.io/docs) and [MongoDB Atlas Provider docs](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs)
