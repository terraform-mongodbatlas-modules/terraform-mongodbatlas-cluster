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

## For Destination Module Developers

**Do not modify synced files directly.** Changes will be overwritten on next sync.

To make changes:
1. Open a PR in the cluster repository
2. After merge, run sync to update destination modules

**Adding module-specific CI:**

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

**Module-specific configuration:**

Edit these files freely:
- `.github/dev/dev_vars.py`
- `docs/examples.yaml`
- `docs/inputs_groups.yaml`

## Running the Sync

From the cluster repository:

```bash
just path-sync --dry-run  # Preview changes
just path-sync            # Apply sync
```

## Why One-Way Sync?

- **Single source of truth:** Cluster team owns shared tooling
- **No merge conflicts:** One-way flow eliminates reconciliation
- **Simpler upgrades:** Update once, sync everywhere
