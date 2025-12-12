# Changelog Process

This module uses [go-changelog](https://github.com/hashicorp/go-changelog) for structured changelog management. 

Each PR with user-facing changes requires a changelog entry file at `.changelog/<PR_NUMBER>.txt`.

**Create entries for:** New features, bug fixes, breaking changes, deprecations, important notes.

**No needed for:** Documentation-only, internal refactoring, CI/CD, test improvements.

A single PR can include multiple changelog entries for distinct changes or when a feature affects multiple areas.

## Workflow

1. Developer creates `.changelog/<PR_NUMBER>.txt` entry file.
2. GitHub Actions validates format on every PR.
3. GitHub Actions updates CHANGELOG.md Unreleased section.
4. Release workflow moves Unreleased section to versioned release.

## Entry Format

```
```release-note:<type>
<prefix>: <sentence>
```
```

### Entry Types

| Type | Purpose |
| --- | --- |
| `breaking-change` | Changes requiring user action. |
| `note` | Important information (security, deprecations, migrations). |
| `enhancement` | New features or improvements. |
| `bug` | Fixes for incorrect behavior. |

### Allowed Prefixes

| Prefix | Format | Example |
| --- | --- | --- |
| `module` | `module: <sentence>` | `module: Adds support for auto-scaling configuration`. |
| `provider/` | `provider/<word>: <sentence>` | `provider/mongodbatlas: Requires minimum version 2.3.0`. |
| `terraform` | `terraform: <sentence>` | `terraform: Updates minimum version to 1.9`. |
| `variable/` | `variable/<word>: <sentence>` | `variable/instance_size: Adds validation for M0 tier`. |
| `output/` | `output/<word>: <sentence>` | `output/connection_strings: Adds private endpoint strings`. |
| `example` | `example: <sentence>` | `example: Adds configuration example`. |
| `example/` | `example/<word>: <sentence>` | `example/basic: Adds basic usage example`. |
| `submodule/` | `submodule/<word>: <sentence>` | `submodule/import: Adds cluster import functionality`. |

Prefixes with `/` require a word after the slash (e.g., `provider/mongodbatlas:` not `provider/:`).

## Breaking Changes

Breaking changes require user action during upgrade.

**Breaking:**
- **Variable changes:** Removing variables, changing types/names/defaults, adding restrictive validation.
- **Output changes:** Removing outputs, changing names or types/structure.
- **Behavior changes:** Changing module defaults, new resources enabled by default, removing moved blocks.
- **Version requirements:** Provider major version upgrade, significant Terraform CLI version upgrade expected to be supported.
- **Module removal:** Removing entire module, variable, output, or submodule (must have migration path and deprecation notice).

```
```release-note:breaking-change
variable/regions: Removes deprecated shard_number attribute
```
```

```
```release-note:breaking-change
provider/mongodbatlas: Requires minimum version 3.0.0
```
```

**Not breaking:**
- **Provider minor upgrades:** Minor version upgrades (e.g., 1.15.0 to 1.16.0) even if user intervention is needed to bump the provider version.
- **Deprecations:** Deprecation notices without configuration changes required.
- **Example changes:** Any changes to examples including removals or breaking changes.
- **EOL version changes:** Changes affecting only EOL Terraform CLI versions.
- **Internal changes:** Resource updates not affecting variables, outputs, or module functionality.
- **API default alignment:** API changes default but module already sets that default.
- **Adding optional features:** New optional variables/outputs with defaults, bug fixes, performance improvements.

## Reference

**Validation rules:**
1. Type in [allowed-types.txt](../.github/changelog/allowed-types.txt), prefix in [allowed-prefixes.txt](../.github/changelog/allowed-prefixes.txt).
2. Format: `<prefix>: <sentence>` (one space after colon).
3. Slash prefixes: `<prefix>/<word>: <sentence>`.
4. Sentence: 3rd person singular, single line, capital first letter, no ending period, no extra whitespace.
5. Only `.changelog/<PR_NUMBER>.txt` created per PR.

**Files:**
- `.changelog/<PR_NUMBER>.txt` - Changelog entries.
- [`.github/changelog/allowed-types.txt`](../.github/changelog/allowed-types.txt) - Valid types.
- [`.github/changelog/allowed-prefixes.txt`](../.github/changelog/allowed-prefixes.txt) - Valid prefixes.
- [`.github/changelog/check-changelog-entry-file/main.go`](../.github/changelog/check-changelog-entry-file/main.go) - Validation script.
- [`.github/workflows/check-changelog-entry-file.yml`](../.github/workflows/check-changelog-entry-file.yml) - Validation workflow.

**Local validation:**
```bash
just check-changelog-entry-file .changelog/123.txt
```
