# SDLC Sync Guide

This guide explains how SDLC tooling is shared from the **cluster module** (source) to other modules (destinations like `atlas-azure`).

## How It Works

The cluster module defines shared tooling in [`.github/sdlc.src.yaml`](../.github/sdlc.src.yaml). The `path-sync` tool copies files one-way from cluster to destination modules.

```
cluster (source) ──sync──> atlas-azure (destination)
                 ──sync──> other-module (destination)
```

Changes to shared tooling must be made in the cluster repository. Destination modules receive updates through sync.

## What Gets Synced

| Category | Paths | Notes |
|----------|-------|-------|
| Python tooling | `.github/{changelog,docs,release,workspace}/` | Excludes `dev_vars.py` |
| Workflows | `.github/workflows/` | Excludes module-specific tests |
| Config | `justfile`, `.pre-commit-config.yaml`, `.terraform-docs.yml` | |
| GitHub | `.github/CODEOWNERS`, `pull_request_template.md`, `ISSUE_TEMPLATE/` | |

**Not synced** (module-specific):
- `.github/dev/dev_vars.py` - workspace paths and test file patterns
- `docs/examples.yaml` - example configuration
- `docs/inputs_groups.yaml` - README input grouping
- `cleanup-test-env.yml`, `dev-integration-test.yml`, `pre-release-tests.yml`

## Sync Modes

| Mode | Behavior |
|------|----------|
| `sync` (default) | Copy if destination missing or source newer |
| `replace` | Always overwrite destination |

## Section Markers (Justfile)

The justfile uses section markers to mix shared and module-specific content:

```makefile
# === OK_EDIT: path-sync header ===
# Module-specific configuration (preserved during sync)
PLAN_TEST_FILES := "-filter=tests/plan_validations.tftest.hcl ..."

# === DO_NOT_EDIT: path-sync standard ===
# Shared recipes (replaced during sync)
pre-commit: fmt validate lint check-docs py-check
    @echo "Pre-commit checks passed"

# === OK_EDIT: path-sync standard ===
# Module-specific recipes below (not synced)
```

| Section | Marker | Behavior |
|---------|--------|----------|
| Header | `OK_EDIT: path-sync header` | Module-specific variables, preserved |
| Standard | `DO_NOT_EDIT: path-sync standard` | Shared recipes, replaced |

## For Destination Module Developers

**Do not modify synced files directly.** Changes will be overwritten on next sync.

### Change Request Options

| Option | Approach | When to use |
|--------|----------|-------------|
| SRC first | PR in cluster repo, wait for sync | Default, maintains single source of truth |
| Dual PR | PR in both azure and cluster (ignore failed validation) | Urgent fixes |
| Opt-out file | Remove path-sync header from file | File becomes DEST-owned, no future syncs |
| Opt-out section | Add section marker in SRC, use `skip_sections` in DEST config | Partial opt-out |

### Module-Specific Configuration

Edit these files freely (not synced):
- `.github/dev/dev_vars.py` - workspace paths and test file patterns
- `docs/examples.yaml` - example table configuration
- `docs/inputs_groups.yaml` - variable groupings

### Adding Module-Specific CI

Create workflows with unique names. Only files matching sync patterns are overwritten:

```yaml
# .github/workflows/my-module-test.yml
# Module-specific workflow - not managed by sync
name: My Module Test
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
```

## Running the Sync

From the cluster repository:

```bash
just sdlc-sync-dry  # Preview changes
just sdlc-sync      # Apply sync
```

## Testing Changes (Source Developers)

To validate synced files work before merging source changes:

1. Create PR in cluster repo with the changes
2. Run `just sdlc-sync` locally (or trigger workflow dispatch from PR branch)
3. Review the changes in DEST repos - their CI will validate the changes
4. If DEST CI passes, merge SRC PR, then commit DEST changes

## Why One-Way Sync?

- **Single source of truth:** Cluster team owns shared tooling
- **No merge conflicts:** One-way flow eliminates reconciliation
- **Simpler upgrades:** Update once, sync everywhere
