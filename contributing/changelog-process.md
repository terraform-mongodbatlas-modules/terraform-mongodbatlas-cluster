# Changelog Process

This guide documents the changelog entry process for the terraform-mongodbatlas-cluster module.

## Overview

This repository uses a structured changelog process based on [go-changelog](https://github.com/hashicorp/go-changelog) to maintain a comprehensive CHANGELOG.md file. The process ensures that all user-facing changes are documented consistently and that release notes can be automatically generated.

### Key Concepts

- **Single top-level CHANGELOG.md** - One changelog file for the entire repository at the root
- **Pull request entries** - Each PR with user-facing changes requires a changelog entry file
- **Automated validation** - GitHub Actions validates entry format automatically
- **Automated release** - Changelog is built automatically from individual entries

### Tools and Workflow

1. **Developer creates entry file** - `.changelog/<PR_NUMBER>.txt` in their PR
2. **GitHub Actions validates format** - Runs on every PR, validates entry syntax
3. **GitHub Action updates CHANGELOG.md** - Adds entry files info to CHANGELOG.md Unreleased section
4. **Release workflow updates CHANGELOG.md version** - Moves Unreleased section to start for the new version

## Creating Changelog Entries

### When to Create an Entry

Create a changelog entry for user-facing changes:

- New features or enhancements
- Bug fixes
- Breaking changes
- Deprecations or removals
- Important notes (e.g., security advisories, migration guides)

Skip changelog entries for:

- Documentation-only changes
- Internal refactoring with no user impact
- CI/CD or tooling updates
- Test improvements

### Entry File Location

Create a file at `.changelog/<PR_NUMBER>.txt` where `<PR_NUMBER>` is your pull request number.

Example: `.changelog/123.txt` for PR #123

### Entry Format

Each entry must follow this format:

```
```release-note:<type>
<prefix>: <sentence>
```
```

**Format rules:**

- **type**: Must be one of: `breaking-change`, `note`, `enhancement`, `bug`
- **prefix**: Must be one of the allowed prefixes (see below)
- **sentence**: Single-line description in 3rd person singular (e.g., "Adds support" not "Add support"), starting with capital letter, no period at end

### Allowed Entry Types

| Type | Purpose | When to Use |
|------|---------|-------------|
| `breaking-change` | Breaking changes requiring user action | API changes, removed features, behavior changes requiring migration |
| `note` | Important information | Security advisories, deprecations, migration guides, important announcements |
| `enhancement` | New features or improvements | New functionality, improved existing features, performance improvements |
| `bug` | Bug fixes | Fixes for incorrect behavior, error handling improvements |

### Allowed Prefixes

Prefixes categorize changes by the area they affect:

| Prefix | Format | Example |
|--------|--------|---------|
| `module` | `module: <sentence>` | `module: Adds support for auto-scaling configuration` |
| `provider/` | `provider/<word>: <sentence>` | `provider/mongodbatlas: Requires minimum version 2.3.0` |
| `terraform` | `terraform: <sentence>` | `terraform: Updates minimum version to 1.9` |
| `variable/` | `variable/<word>: <sentence>` | `variable/instance_size: Adds variable for cluster instance size` |
| `output/` | `output/<word>: <sentence>` | `output/connection_strings: Adds output with connection strings` |
| `example` | `example: <sentence>` | `example: Improves format for all examples` |
| `example/` | `example/<word>: <sentence>` | `example/basic: Adds basic usage example` |
| `submodule/` | `submodule/<word>: <sentence>` | `submodule/import: Adds cluster import functionality` |

## Type Classification Matrix

This matrix shows which prefixes are commonly used with each type:

| Type | Typical Prefixes | Usage Notes |
|------|------------------|-------------|
| `breaking-change` | `module`, `variable/`, `output/`, `submodule/` | Use for changes requiring user action or migration |
| `note` | `module`, `example`, `submodule/`, `provider/`, `terraform` | Use for important information, deprecations, advisories |
| `enhancement` | `module`, `variable/`, `output/`, `example`, `example/`, `submodule/` | Use for new features and improvements |
| `bug` | `module`, `provider/`, `variable/`, `output/`, `example/`, `submodule/` | Use for fixes to incorrect behavior |

## Breaking Change Classification

A breaking change is any modification that:

1. **Changes existing behavior** in a way that may break user configurations
2. **Removes functionality** that users may depend on
3. **Changes resource attributes** in incompatible ways
4. **Requires manual intervention** during upgrade

### Breaking Change Categories

#### 1. Variable Changes

**Breaking:**
- Removing a variable
- Changing variable type (e.g., `string` → `list(string)`)
- Removing variable default (making it required)
- Adding validation that rejects previously valid values
- Changing variable behavior significantly

**Example:**
```
```release-note:breaking-change
variable/regions: Removes deprecated shard_number attribute
```
```

**Not Breaking:**
- Adding a new optional variable with a default
- Making a required variable optional by adding a default
- Improving variable description
- Adding validation that only rejects invalid values

#### 2. Output Changes

**Breaking:**
- Removing an output
- Changing output type or structure
- Changing output structure

**Example:**
```
```release-note:breaking-change
output/cluster: Changes structure to include additional metadata
```
```

**Not Breaking:**
- Adding a new output
- Adding attributes to an existing output object

#### 3. Module Behavior Changes

**Breaking:**
- Changing default resource configuration
- Removing or significantly changing features
- Changing how module interprets input
- Requiring new required variables

**Example:**
```
```release-note:breaking-change
module: Changes auto-scaling defaults to M20-M400 range
```
```

**Not Breaking:**
- Bug fixes that restore intended behavior
- Adding new optional features
- Performance improvements without behavior changes
- Extending functionality without changing existing behavior

#### 4. Terraform Version Requirements

**Breaking:**
- Increasing minimum Terraform version
- Increasing minimum provider version

**Example:**
```
```release-note:breaking-change
terraform: Updates minimum required version to 1.10
```
```

#### 5. Experimental Submodules

**Special case**: Experimental submodules (e.g., `submodule/cluster_import`) are allowed to introduce breaking changes as long as they are clearly marked.

**Example:**
```
```release-note:breaking-change
submodule/import: Changes import workflow to use data source
```
```

### Breaking Change Examples

#### Variable Removal
```
```release-note:breaking-change
variable/old_config: Removes deprecated old_config variable
```
```

**Migration guide**: Users must migrate to `new_config` variable. See [migration docs](link).

#### Variable Type Change
```
```release-note:breaking-change
variable/regions: Changes type from list(string) to list(object)
```
```

**Migration guide**: Update region definitions from `["US_EAST_1"]` to `[{name = "US_EAST_1"}]`.

#### Validation Change
```
```release-note:breaking-change
variable/instance_size: Adds validation to reject M0, M2, M5 tiers
```
```

**Migration guide**: Free and shared tiers are no longer supported. Upgrade to M10 or higher.

#### Behavior Change
```
```release-note:breaking-change
module: Enables auto-scaling by default
```
```

**Migration guide**: Set `auto_scaling_enabled = false` to preserve previous behavior.

#### Terraform Version Bump
```
```release-note:breaking-change
terraform: Updates minimum required version from 1.7 to 1.9
```
```

**Migration guide**: Upgrade Terraform to version 1.9 or later.

## Validation and Automation

### GitHub Actions Workflow

The repository includes a GitHub Actions workflow (`.github/workflows/check-changelog-entry-file.yml`) that automatically validates changelog entries on every pull request.

**Validation checks:**

1. **File location** - Only `.changelog/<PR_NUMBER>.txt` should be modified
2. **Entry format** - Type, prefix, and sentence format must be correct
3. **Type validity** - Type must be in `allowed-types.txt`
4. **Prefix validity** - Prefix must be in `allowed-prefixes.txt`
5. **Sentence format** - No period at end, single line, no leading/trailing whitespace

### Running Validation Locally

Test your changelog entry before pushing:

```bash
# Validate changelog entry file (replace with your PR number)
just check-changelog-entry-file .changelog/123.txt
```

Expected output for valid entry:
```
Changelog entry is valid
```

## Multiple Entries in One PR

You can include multiple changelog entries in a single PR for different types of changes:

```
```release-note:enhancement
module: Adds support for auto-scaling configuration
```

```release-note:bug
provider/mongodbatlas: Fixes authentication retry logic
```

```release-note:breaking-change
variable/instance_size: Removes support for M0, M2, M5 tiers
```
```

**Best practices:**
- Group related changes under the most appropriate type
- Use multiple entries only when changes are distinct and significant
- Prefer combining related changes into a single entry when possible

## Reference

### File Locations

- **Changelog entries**: `.changelog/<PR_NUMBER>.txt`
- **Allowed types**: `.github/changelog/allowed-types.txt`
- **Allowed prefixes**: `.github/changelog/allowed-prefixes.txt`
- **Validation script**: `.github/changelog/check-changelog-entry-file/main.go`
- **Validation tests**: `.github/changelog/check_changelog_entry_file_test.py`
- **Workflow**: `.github/workflows/check-changelog-entry-file.yml`
- **Generated changelog**: `CHANGELOG.md`

### Just Commands

```bash
# Validate changelog entry
just check-changelog-entry-file .changelog/<PR_NUMBER>.txt

# Build CHANGELOG.md from entries
just build-changelog

# Run Python tests (includes changelog validation tests)
just py-test
```

### Format Specification

```
```release-note:<type>
<prefix>: <sentence>
```
```

- **type**: `breaking-change` | `note` | `enhancement` | `bug`
- **prefix**: One of the allowed prefixes (see allowed-prefixes.txt)
- **sentence**: Single-line description in 3rd person singular
  - Must start with capital letter
  - Must use 3rd person singular form (e.g., "Adds support" not "Add support")
  - Must not end with period
  - No leading/trailing whitespace
  - No newlines

### Validation Rules

1. Entry type must be in `allowed-types.txt`
2. Entry prefix must be in `allowed-prefixes.txt`
3. Format must be `<prefix>: <sentence>` (exactly one space after colon)
4. Prefix with `/` must have format `<prefix>/<word>: <sentence>`
5. Sentence must be single line (no `\n`)
6. Sentence must not have leading or trailing whitespace
7. Sentence must not end with period
8. Only `.changelog/<PR_NUMBER>.txt` should be modified (matches PR number)
