# SDLC tooling (`tools/`)

Python scripts, templates, and shared automation for module development, CI, changelog, docs, release, and workspace tests.

Most of this tree is copied from the [cluster module](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster) via [path-sync](https://github.com/EspenAlbert/path-sync). See the [SDLC Sync Guide](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.4.0/contributing/sdlc-sync.md) for how sync works, what is included, and how to request changes.

## Do not edit synced files in destination modules

In destination modules (for example `atlas-aws`, `atlas-azure`, `project`), changes to synced files are overwritten on the next sync. Make shared tooling changes in the cluster repository, then run `just sdlc-sync` from cluster.

## How to tell if a file is synced

- The first line is `# path-sync copy -n sdlc`.
- Or the path is listed in [`.github/sdlc.src.yaml`](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.4.0/.github/sdlc.src.yaml).

## Module-specific exceptions

These paths are not synced or are scaffolded per module:

- `tools/dev/dev_vars.py` — workspace paths and test file patterns (scaffolded; edit locally).
- `tools/dev/*.json`, `variables_generated.tf` — generated region artifacts (azure/gcp only).

## Cluster-only tooling

`tools/tf_gen/` exists only in the cluster repository and is not part of SDLC sync. See [tools/tf_gen/README.md](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/blob/v0.4.0/tools/tf_gen/README.md).
