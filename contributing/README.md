<!-- === OK_EDIT: path-sync header === -->
# Contributing Guides

This directory contains guides for contributors to the terraform-mongodbatlas-cluster module.

## Available Guides

- **[Development Guide](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.3.0/contributing/development-guide.md)** - Quick start, development workflow, and release process
- **[Test Guide](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.3.0/contributing/test-guide.md)** - Running unit, integration, and plan snapshot tests
<!-- === DO_NOT_EDIT: path-sync default === -->
- **[Documentation Guide](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.3.0/contributing/documentation-guide.md)** - Working with auto-generated documentation
- **[Changelog Guide](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.3.0/contributing/changelog-process.md)** - Creating changelog entries and understanding the changelog workflow
- **[SDLC Sync Guide](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.3.0/contributing/sdlc-sync.md)** - How tooling is shared between Terraform modules

## Quick Start

```bash
# Install required tools
brew install just terraform tflint terraform-docs uv
just pre-commit
```

## Getting Help

- Check [Issues](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.3.0/../../../issues) for similar problems
- Create new issue with output from `just pre-commit` if needed
- See [Terraform docs](https://www.terraform.io/docs) and [MongoDB Atlas Provider docs](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs)
<!-- === OK_EDIT: path-sync default === -->
