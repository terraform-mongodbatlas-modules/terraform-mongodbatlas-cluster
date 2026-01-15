# Contributing to terraform-mongodbatlas-cluster

Thank you for your interest in contributing to this Terraform module!

## Contributing Guides

All contributing documentation has been organized in the [`contributing/`](contributing/) directory:

- **[Development Guide](contributing/development-guide.md)** - Quick start, development workflow, and release process
- **[Test Guide](contributing/test-guide.md)** - Running unit, integration, and plan snapshot tests
- **[Documentation Guide](contributing/documentation-guide.md)** - Working with auto-generated documentation
- **[Changelog Guide](contributing/changelog-process.md)** - Creating changelog entries and understanding the changelog workflow
- **[SDLC Sync Guide](contributing/sdlc-sync.md)** - How tooling is shared between Terraform modules

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

See the [Development Guide](contributing/development-guide.md) for detailed instructions.
