# Adding a New Terraform Module Repository

Step-by-step guide for adding a new repository to the [terraform-mongodbatlas-modules](https://github.com/terraform-mongodbatlas-modules) organization with SDLC tooling.

## Prerequisites

Before starting, ensure:
- The GitHub repo exists in the `terraform-mongodbatlas-modules` organization (created via [terraform-mongodbatlas-modules-management](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-modules-management)).
- You have push access to the cluster repo (source of SDLC sync).
- You have a local clone of the cluster repo with the destination repo checked out as a sibling directory (e.g., `../gcp` relative to cluster).

If the repo does not exist yet, add a `.tf` file in the management repo's `modules/` directory copying an existing file, e.g., `atlas-gcp-repository.tf`, remember to update:
- `name`.
- `description`.

Then add the resource reference to `locals.repositories` in `modules/main.tf`.

## Step 1: Add Destination to `sdlc.src.yaml`

In the cluster repo, edit `.github/sdlc.src.yaml` and add a new entry under `destinations:`.

Required fields:
- `name` - short identifier used in sync PR titles and `--dest` flag.
- `repo_url` - full GitHub URL of the destination repo.
- `dest_path_relative` - relative path from cluster repo to the local clone (e.g., `../gcp`).
- `default_branch` - typically `main`.

Optional fields:
- `include_groups` - list of `path_groups` to include for this destination. Available groups:
  - `regions` - region extraction files (`extract_regions.py`, `validate-region-mappings.yml`). Include for CSP modules with region mappings (azure, gcp).
  - `project_generator` - workspace test project generator. Include for modules with workspace tests.
  - `pre_release` - `pre-release-tests.yml` workflow. Include for modules that run pre-release apply/destroy tests. Omit for repos without examples (e.g., org).
- `skip_sections` - map of `file: [section-ids]` to skip specific sections per file.

### Example: Destination with Groups and Section Skipping

```yaml
destinations:
  - name: gcp
    repo_url: https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-atlas-gcp
    dest_path_relative: ../gcp
    default_branch: main
    include_groups: [regions, project_generator, pre_release]
    skip_sections:
      justfile: [dev-vars-org]
```

### Deciding What to Include/Skip

**`include_groups`** - opt-in for file groups the module needs:

| Group | When to include |
|-------|-----------------|
| `regions` | Module has CSP region mappings (e.g., azure, gcp). |
| `project_generator` | Module has workspace tests that need project generation. |
| `pre_release` | Module has examples for apply/destroy pre-release testing. |

**`justfile` sections** - skip sections the module does not need:

| Section | When to skip |
|---------|--------------|
| `dev-vars-org` | Module does not need `org_id` in dev.tfvars. |
| `regions` | Module has no region mappings (e.g., project, org). |

**`.github/workflows/code-health.yml` sections** - skip jobs not yet ready:

| Section | When to skip |
|---------|--------------|
| `job-snapshot-tests` | No workspace/plan-snapshot tests configured yet. |
| `job-slack` | No `SLACK_WEBHOOK_URL` secret configured yet. |

When the module is ready for these features, remove from `skip_sections` and re-sync.

## Step 2: Run SDLC Sync from Branch

Create a branch in the cluster repo and run the sync targeting only the new destination:

```bash
git checkout -b add-<name>-destination
# Edit .github/sdlc.src.yaml as described above
git add .github/sdlc.src.yaml
git commit -m "chore: add <name> to sdlc destinations"

# Sync only the new destination (creates a PR in the destination repo)
just sdlc-sync -d <dest-name>
```

The sync will:
1. Copy all synced files to the destination repo.
2. Run verify steps (`just uv-sync`, `just docs`).
3. Commit changes and create a PR in the destination repo.

Alternatively, trigger the `SDLC Copy` workflow via `workflow_dispatch` from your branch in GitHub Actions. Use the `extra-args` input to target specific destinations (e.g., `-d gcp` or `-d gcp -d azure`), or leave it empty to sync all.

## Step 3: Customize the Generated PR

In the destination repo, the sync creates a PR on a `sync/sdlc` branch. Switch to that branch and make module-specific edits:

1. **`pre-release-tests.yml` env vars** - if you included `pre_release`, add CSP-specific env vars after the `OK_EDIT: path-sync env` marker, indented under `env:` (e.g., `GCP_PROJECT_ID` for gcp, `AWS_ACCESS_KEY_ID` for aws). See the [gcp workflow](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-atlas-gcp/blob/main/.github/workflows/pre-release-tests.yml) for reference.
2. **`pre-release-tests.yml` apply steps** - after the `OK_EDIT: path-sync job-apply-setup` marker in the `apply-and-destroy` steps, add CSP-specific setup (e.g., GCP workload identity auth) and customize `dev-vars-*` / example commands. Job-level config like `permissions` goes before `steps:` after the first `OK_EDIT: path-sync job-apply-setup` marker at job level.
3. Commit and push:
   ```bash
   git add .
   git commit -m "chore: customize pre-release workflow for <module>"
   git push
   ```

The [template](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-module-template) repo includes a minimal `justfile` with `PLAN_TEST_FILES := ""`, so no manual override is needed. `.gitignore` is synced automatically via section markers.

> If the repo was created from an older template version, delete any stale workflows (`terraform-test.yml`, `terraform-code-lint.yml`) that are now replaced by `code-health.yml`.

## Step 4: Sync GitHub Secrets

The destination repo needs secrets for CI workflows to function. Use [GitHub CLI](https://cli.github.com/) to set them from a secrets file:

```bash
cd <destination-repo>
gh secret set -f <secrets-file>.env
# you can find the "base" file in our secrets manager, search for "terraform-mongodbatlas-modules"
```

> **Warning**: Do not commit the `.env` secrets file to git. Ensure it is listed in `.gitignore` or stored outside the repo directory.

## Step 5: Merge and Tag

After the sync PR passes CI and is reviewed:

1. Merge the PR in the destination repo.
2. Create the `changelog-dir-created` tag (required for changelog tooling to determine the initial commit range):
   ```bash
   cd <destination-repo>
   git checkout main
   git pull
   git tag changelog-dir-created
   git push origin changelog-dir-created
   ```
3. Merge the cluster repo PR that added the destination to `sdlc.src.yaml`.

## Step 6: Publish to Terraform Registry

This step is only needed when the module is ready for its first release.

1. **Add GitHub App access**: Go to an existing published module's [Settings > GitHub Apps](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster/settings/installations), click `Configure` on `Terraform Cloud`, and add the new repository.
2. **Publish the module**: Follow the instructions in the [terraform-mongodbatlas-modules-management README](https://github.com/terraform-mongodbatlas-modules/terraform-mongodbatlas-modules-management#publishing-a-new-module-to-the-terraform-registry).
