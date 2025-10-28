# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `.tflint.hcl` configuration file for consistent linting across contributors
- `.env.example` file documenting required environment variables
- `CHANGELOG.md` to track changes between versions
- `.pre-commit-config.yaml` for automated code quality checks
- `CLAUDE.md` documentation for AI-assisted development
- `sensitive = true` flag to `connection_strings` output to prevent credential leaks

### Fixed
- Inconsistent `module_version` in example 12 (changed from `0.0.1` to `0.1.0`)
- Duplicate GEOSHARDED validation logic in `main.tf` (lines 244-246)
- Provider version mismatch between root module (`~> 2.0`) and tests (`~> 2.1`)
- TODO comment in `output.tf` now includes description of intended work

### Changed
- TODO comment in `output.tf` now more descriptive (CLOUDP-351551)

## [0.1.0] - 2025-10-28

### Added
- Initial public preview release
- Support for REPLICASET, SHARDED, and GEOSHARDED cluster types
- Simplified `regions` variable for easier cluster topology definition
- Alternative `replication_specs` variable for advanced configurations
- Auto-scaling support with Architecture Center recommended defaults
- Production-ready security defaults (backups, PIT, TLS 1.2, etc.)
- 12 comprehensive examples covering various deployment scenarios
- Terraform test framework integration with unit and integration tests
- Documentation generation with terraform-docs
- Development workflow automation with `just` command runner

### Module Features
- Automatic priority assignment for regions within shards/zones
- Flexible shard count management via `shard_count` or explicit `shard_number`
- Support for analytics nodes with separate auto-scaling configuration
- Multi-cloud and multi-region cluster support
- Comprehensive input validation with helpful error messages
- Provider metadata tracking for usage analytics

### Documentation
- Comprehensive README with examples and variable documentation
- CONTRIBUTING.md with development setup instructions
- Example-specific READMEs for each deployment scenario
- Inline code documentation and comments

### Testing
- Unit tests for auto-scaling configurations
- Unit tests for region variable transformations
- Unit tests for replication_specs validation
- Integration tests for cluster creation and management

### Known Limitations
- This is a public preview (v0) release
- Upgrades from v0 to v1 may not be seamless
- M0/M2/M5 free tier clusters are not supported
- V1 release with long-term upgrade support planned for early 2026

## Notes

### Public Preview Disclaimer

The MongoDB Atlas Cluster Module is currently in Public Preview. While it is functional and embeds MongoDB best practices, it is subject to changes before the v1 release. We welcome feedback and contributions during this preview phase.

### Migration to V1

When v1 is released, it will include:
- Long-term upgrade support
- Backward compatibility guarantees
- Stable API surface
- Production support from MongoDB

### Versioning Strategy

- **v0.x** - Public preview releases, may include breaking changes
- **v1.0.0+** - Production releases with semantic versioning and upgrade support

[Unreleased]: https://github.com/mongodb/modules-terraform-mongodbatlas-cluster/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/mongodb/modules-terraform-mongodbatlas-cluster/releases/tag/v0.1.0
