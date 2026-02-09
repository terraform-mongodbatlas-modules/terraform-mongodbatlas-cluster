<!-- === OK_EDIT: path-sync header === -->
# Contributing Guides

This directory contains guides for contributors to the terraform-mongodbatlas-cluster module.

## Available Guides

- **[Development Guide](development-guide.md)** - Quick start, development workflow, and release process
- **[Test Guide](test-guide.md)** - Running unit, integration, and plan snapshot tests
- **[New Repo Guide](new-repo-guide.md)** - Adding a new module repository with SDLC tooling
<!-- === DO_NOT_EDIT: path-sync default === -->
- **[Documentation Guide](documentation-guide.md)** - Working with auto-generated documentation
- **[Changelog Guide](changelog-process.md)** - Creating changelog entries and understanding the changelog workflow
- **[SDLC Sync Guide](sdlc-sync.md)** - How tooling is shared between Terraform modules

## Quick Start

```bash
# Install required tools
brew install just terraform tflint terraform-docs uv
just pre-commit
```

## Getting Help

- Check [Issues](../../../issues) for similar problems
- Create new issue with output from `just pre-commit` if needed
- See [Terraform docs](https://www.terraform.io/docs) and [MongoDB Atlas Provider docs](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs)
<!-- === OK_EDIT: path-sync default === -->
