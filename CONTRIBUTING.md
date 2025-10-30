# Contributing to terraform-mongodbatlas-cluster

This guide will help you set up your development environment for contributing to this Terraform module.

## Prerequisites

- **macOS** with [Homebrew](https://brew.sh/) installed
- **Git**: For version control
- **Python 3.10+**: For documentation generation scripts
- **uv**: Python package installer
- **MongoDB Atlas Account**: For testing (optional, but recommended)

## Development Tools Installation

This project uses several tools for development, testing, and documentation. All commands are managed through [just](https://just.systems/) - a command runner similar to `make`.

Install all required tools with Homebrew:

```bash
# Install just (command runner)
brew install just

# Install Terraform
brew tap hashicorp/tap
brew install hashicorp/tap/terraform

# Install TFLint (Terraform linter)
brew install tflint
# Install terraform-docs (documentation generator)
brew install terraform-docs
# Install uv (python script runner)
brew install uv
```

## Environment Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-org/terraform-mongodbatlas-cluster.git
   cd terraform-mongodbatlas-cluster
   ```

2. **Create environment file** (optional):
   ```bash
   cp .env.example .env
   # Edit .env with your specific configurations
   ```

3. **Verify tool installations:**
   ```bash
   just --version
   terraform --version
   tflint --version
   terraform-docs --version
   ```

## Development Workflow

### Available Commands

Run `just` or `just --list` to see all available commands:

```bash
# List all available commands
just

# Format all Terraform files
just fmt

# Validate Terraform configuration
just validate

# Run linting checks
just lint

# Generate documentation
just docs

# Generate only root README (TOC and tables)
just gen-readme

# Generate only example documentation
just gen-examples

# Check if documentation is up-to-date (CI mode)
just gen-readme --check
just gen-examples --check

# Run all checks (format, validate, lint, docs)
just check

# Initialize all example configurations
just init-examples

# Plan all examples (requires MongoDB Atlas project ID)
just plan-examples <your-project-id>

# Create a release (maintainers only)
just release-commit v1.0.0
```

### Development Process

1. **Before making changes:**
   ```bash
   # Format and validate your code
   just fmt
   just validate
   ```

2. **During development:**
   ```bash
   # Run linting to catch issues early
   just lint
   ```

3. **Before committing:**
   ```bash
   # Run all checks
   just check
   ```

4. **Testing with examples:**
   ```bash
   # Initialize examples
   just init-examples
   
   # Test with your MongoDB Atlas project
   just plan-examples YOUR_PROJECT_ID
   ```

### Configuration Files

- **`.terraform-docs.yml`**: Configuration for documentation generation
- **`examples/tags.tfvars`**: Common tags for testing examples

> **Note**: No TFLint configuration file (`.tflint.hcl`) currently exists, so TFLint runs with default rules.

## Testing

### Prerequisites for Testing

- **MongoDB Atlas Project ID**: Required for testing examples
- **Atlas Service Account credentials** (for provider auth during tests): client id/secret
- **Atlas Organization ID** (for apply tests): where the test project will be created

### Running Manual Examples

```bash
# Initialize all examples
just init-examples

# Plan all examples (dry run)
just plan-examples YOUR_PROJECT_ID

# Apply specific example (be careful!)
cd examples/01_single_region
terraform apply -var project_id=YOUR_PROJECT_ID -var-file=../tags.tfvars
```

### Running Local Tests with `terraform test`

The Terraform test framework validates the module locally. Tests are defined under [`/tests`](./tests).

1. Export provider authentication via environment variables:

```bash
export MONGODB_ATLAS_CLIENT_ID=your_sa_client_id
export MONGODB_ATLAS_CLIENT_SECRET=your_sa_client_secret
# Optional:
export MONGODB_ATLAS_BASE_URL=https://cloud.mongodb.com/
```

2. Provide org id to tests via environment variable:

```bash
export MONGODB_ATLAS_ORG_ID=<YOUR_MONGODB_ATLAS_ORG_ID>

# Run all tests (unit + integration)
just test

# Run only unit/plan tests (no resources created)
just unit-plan-tests

# Run only integration/apply tests (creates and destroys resources)
just integration-tests
```

**Test Types**:

1. **Unit Tests** (`unit-plan-tests`): Validate the module's configuration and expected plan output. No resources are created.
2. **Integration Tests** (`integration-tests`): Perform full integration tests by creating and destroying resources.

**Important:** For `apply` tests, make sure you set `termination_protection_enabled = false` in the `variables` portion of the `run` block, otherwise the test will fail when trying to delete the cluster as part of cleanup stage of the test.

## Documentation Generation

This project uses automated scripts to generate and maintain documentation consistency. All documentation generation scripts are located in `.github/` and are written in Python.

### Documentation Tools

1. **Root README Generator** (`.github/root_readme.py`)
   - Generates Table of Contents (TOC) from markdown headings
   - Generates example tables from `.terraform-docs.yml` configuration
   - Automatically extracts `cluster_type` from example `main.tf` files
   - Updates `<!-- BEGIN_TOC -->...<!-- END_TOC -->` sections
   - Updates `<!-- BEGIN_TABLES -->...<!-- END_TABLES -->` sections

2. **Example Documentation Generator** (`.github/examples_readme.py`)
   - Generates `README.md` for each example using `docs/example_readme.md` template
   - Generates `versions.tf` for each example based on root `versions.tf`
   - Reads example names and metadata from `.terraform-docs.yml`
   - Skips examples with custom configurations (e.g., `08_development_cluster`)

3. **Markdown Link Converter** (`.github/md_link_absolute.py`)
   - Converts relative markdown links to absolute GitHub URLs
   - Used during release process to create version-specific links
   - Respects `.gitignore` and skips specified files

### Generating Documentation

```bash
# Generate all documentation (ROOT README + examples)
just docs

# Generate only root README (TOC and tables)
just gen-readme

# Generate only example documentation
just gen-examples

# Preview changes without modifying files
just gen-readme --dry-run
just gen-examples --dry-run
```

### Documentation Workflow for Contributors

1. **During Development:**
   - Modify code, variables, or examples as needed
   - Documentation will be auto-generated as part of `just check`

2. **Before Committing:**
   ```bash
   # This will regenerate all docs and format everything
   just check
   ```

3. **Pull Request Checks:**
   - CI automatically verifies documentation is up-to-date using `--check` mode
   - The check compares generated docs against committed files
   - If docs are outdated, the check fails with exit code 1 and shows what needs updating
   - To fix: run `just docs` locally and commit the changes

   ```bash
   # Verify docs are up-to-date (same as CI runs)
   just gen-readme --check
   just gen-examples --check
   ```

### Documentation Configuration

- **`.terraform-docs.yml`**: Controls documentation generation
  - Defines example tables structure
  - Specifies display names and metadata
  - Supports `title_suffix` for enhanced naming (e.g., "Local" vs "Global")
- **`docs/example_readme.md`**: Template for example README files
- **Example folder naming**: Format `NN_descriptive_name` where `NN` is the folder number

### Adding New Examples

When adding a new example:

1. Create folder with format: `NN_descriptive_name`
2. Add entry to `.terraform-docs.yml` under appropriate table:
   ```yaml
   - folder: NN
     name: Descriptive Name
     title_suffix: (Optional Details)  # optional
     cluster_type: SHARDED  # optional, auto-detected from main.tf
   ```
3. Run `just docs` to generate documentation
4. The `cluster_type` will be automatically extracted from `main.tf` if not specified in config

## Code Style and Standards

- **Terraform formatting**: Use `terraform fmt` (automated via `just fmt`)
- **Variable naming**: Use snake_case for variables and resources
- **Documentation**: All variables and outputs must be documented
- **Examples**: Each example should be self-contained and documented

## Release Process

Releases are created on separate release branches with version-specific documentation.

### Creating a Release

Use the `release-commit` command to prepare a release:

```bash
# Create release branch, update version, regenerate docs, and tag
just release-commit v1.0.0
```

This command will:
1. Create and checkout a new release branch `v1.0.0`
2. Update `module_version` in root `versions.tf`
3. Regenerate all example `versions.tf` files (inherit from root)
4. Regenerate root README with updated tables and TOC
5. Convert all relative markdown links to absolute GitHub URLs pointing to `v1.0.0` tag
6. Format all files
7. Commit all changes with message `chore: release v1.0.0`
8. Create git tag `v1.0.0` on the commit

### Pushing the Release

After reviewing the changes:

```bash
# Push the release branch and tag
git push origin v1.0.0 --tags
```

### Release Branch Strategy

- **Main branch**: Always uses relative links (development-friendly)
- **Release branches** (e.g., `v1.0.0`): Use absolute links pointing to specific tag
- Each release is self-contained on its own branch
- Easy to maintain and patch old versions if needed

### Why Absolute Links on Release Branches?

Absolute links ensure documentation stability:
- Links always point to the exact code version they document
- Documentation remains accessible even if files are moved later
- Users can confidently reference specific versions

The links (e.g., `github.com/.../blob/v1.0.0/file.md`) work correctly because:
- The tag `v1.0.0` points to the commit containing those links
- Both the tag and its documentation are pushed together
- GitHub resolves the links to the tagged snapshot

## Submitting Changes

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes and test:**
   ```bash
   just check
   just init-examples
   just plan-examples YOUR_PROJECT_ID
   ```

3. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

4. **Push and create a pull request:**
   ```bash
   git push origin feature/your-feature-name
   ```

## Troubleshooting

### Common Issues

1. **TFLint errors**: TFLint runs with default rules (no custom configuration file exists)
2. **Terraform validation errors**: Ensure all required variables are defined
3. **Documentation generation issues**: Verify `.terraform-docs.yml` configuration

### Getting Help

- Check existing [Issues](../../issues) for similar problems
- Create a new issue with detailed description and include output from `just check`

## Additional Resources

- [Terraform Documentation](https://www.terraform.io/docs)
- [MongoDB Atlas Provider Documentation](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs)
