# Contributing to terraform-mongodbatlas-cluster

This guide will help you set up your development environment for contributing to this Terraform module.

## Prerequisites

- **macOS** with [Homebrew](https://brew.sh/) installed
- **Git**: For version control
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
# Note that some generation steps of the docs are in an alpha phase and will be followed up in CLOUDP-353173:  
# - the generation of docs/inputs.md
# - the README.md sections of <!-- BEGIN/END_TABLES --> and <!-- BEGIN/END_TOC -->

# Run all checks (format, validate, lint, docs)
just check

# Initialize all example configurations
just init-examples

# Plan all examples (requires MongoDB Atlas project ID)
just plan-examples <your-project-id>
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

## Code Style and Standards

- **Terraform formatting**: Use `terraform fmt` (automated via `just fmt`)
- **Variable naming**: Use snake_case for variables and resources
- **Documentation**: All variables and outputs must be documented
- **Examples**: Each example should be self-contained and documented

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
