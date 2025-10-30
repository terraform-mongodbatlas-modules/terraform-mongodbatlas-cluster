# Contributing to terraform-mongodbatlas-cluster

Quick guide for contributing to this Terraform module.

## Quick Start

```bash
# Install required tools (macOS)
brew install just terraform tflint terraform-docs uv

# Clone and setup
git clone <repo-url>
cd terraform-mongodbatlas-cluster

# Verify installation
just

# Before committing
just check
```

**Tools**: [just](https://just.systems/) • [Terraform](https://www.terraform.io/) • [TFLint](https://github.com/terraform-linters/tflint) • [terraform-docs](https://terraform-docs.io/) • [uv](https://docs.astral.sh/uv/)

## Prerequisites

- macOS with [Homebrew](https://brew.sh/) or Linux
- [Git](https://git-scm.com/) for version control
- [uv](https://docs.astral.sh/uv/) Python installer (for doc generation)
- [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) Account (for testing, optional)

## Development Workflow

```bash
# Daily workflow
just fmt                      # Format code
just lint                     # Run linters
just check                    # Run all checks (fmt, validate, lint, check-docs)

# Documentation
just docs                     # Generate all docs
just check-docs               # Verify docs are up-to-date (CI mode)

# Testing
just init-examples            # Initialize examples
just plan-examples PROJECT_ID # Test examples
just test                     # Run unit + integration tests

# Release (maintainers)
just release-commit v1.0.0    # Create release branch
```

Run `just --list` for all commands.

## Testing

### Setup

```bash
# Required for tests (see Atlas Provider authentication docs)
export MONGODB_ATLAS_CLIENT_ID=your_sa_client_id
export MONGODB_ATLAS_CLIENT_SECRET=your_sa_client_secret
# Optional:
export MONGODB_ATLAS_BASE_URL=https://cloud.mongodb.com/

# Run tests
just test                # All tests
just unit-plan-tests     # Plan-only (no resources)
just integration-tests   # Apply tests (creates resources)
```

**Note**: Integration tests set `termination_protection_enabled = false` to allow cleanup.

See [MongoDB Atlas Provider Authentication](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs#authentication) for more details.

## Documentation

Documentation is auto-generated. Run `just check` before committing - it regenerates all docs and verifies they're up-to-date.

### Adding New Examples

1. Create folder: `NN_descriptive_name`
2. Add to `.terraform-docs.yml`:
   ```yaml
   - folder: NN
     name: Descriptive Name
     title_suffix: (Optional)  # e.g., "(AWS + Azure)"
   ```
3. Run `just docs`

**Scripts** (in `.github/`, [Python](https://www.python.org/) 3.10+):
- `root_readme.py` - Generates TOC and tables
- `examples_readme.py` - Generates example docs
- `md_link_absolute.py` - Converts links for releases

## Release Process (Maintainers)

```bash
# Create release branch with version-specific docs
just release-commit v1.0.0

# Review and push
git push origin v1.0.0 --tags
```

**What happens**:
1. Creates release branch `v1.0.0`
2. Updates `module_version` in `versions.tf`
3. Regenerates all docs with absolute links
4. Commits and tags

**Why separate branches?**
- Main uses relative links (dev-friendly)
- Release branches use absolute links (stable docs for that version)

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

- Check [Issues](../../issues) for similar problems
- Create new issue with output from `just check` if needed
- See [Terraform docs](https://www.terraform.io/docs) and [MongoDB Atlas Provider docs](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs)
