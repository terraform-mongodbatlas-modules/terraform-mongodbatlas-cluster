# Contributing Guides

This directory contains guides for contributors to the terraform-mongodbatlas-cluster module.

## Available Guides

- **[Development Guide](development-guide.md)** - Quick start, development workflow, and release process
- **[Test Guide](test-guide.md)** - Running unit, integration, and plan snapshot tests
- **[Documentation Guide](documentation-guide.md)** - Working with auto-generated documentation
- **[Changelog Guide](changelog-process.md)** - Creating changelog entries and understanding the changelog workflow

## Quick Start

```bash
# Install required tools
brew install just terraform tflint terraform-docs uv

# Clone and setup
git clone <repo-url>
cd terraform-mongodbatlas-cluster

# Before committing
just check
```

## Getting Help

- Check [Issues](../../../issues) for similar problems
- Create new issue with output from `just check` if needed
- See [Terraform docs](https://www.terraform.io/docs) and [MongoDB Atlas Provider docs](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs)
