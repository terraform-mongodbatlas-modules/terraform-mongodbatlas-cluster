# path-sync copy -n sdlc

# === OK_EDIT: path-sync header ===
# Module-specific configuration
PLAN_TEST_FILES := "-filter=tests/plan_auto_scaling.tftest.hcl -filter=tests/plan_regions.tftest.hcl -filter=tests/plan_replication_spec.tftest.hcl -filter=tests/plan_geosharded_multi_shard.tftest.hcl -filter=tests/plan_sharded.tftest.hcl -filter=tests/plan_backup_pit.tftest.hcl"

# === DO_NOT_EDIT: path-sync core ===
set dotenv-load

gh_dir := justfile_directory() + "/.github"
uv_gh := "uv run --project .github"
py := "PYTHONPATH=" + gh_dir + " " + uv_gh + " python -m"

default:
    just --list
# === OK_EDIT: path-sync core ===

# === DO_NOT_EDIT: path-sync checks ===
# CHECKS
pre-commit: fmt py-check validate lint check-docs
    @echo "Pre-commit checks passed"

pre-push: pre-commit unit-plan-tests py-test
    @echo "Pre-push checks passed"
# === OK_EDIT: path-sync checks ===

# === DO_NOT_EDIT: path-sync dev-setup ===
# DEV SETUP
uv-sync:
    uv sync --project .github
# === OK_EDIT: path-sync dev-setup ===

# === DO_NOT_EDIT: path-sync formatting ===
# FORMATTING
fmt:
    terraform fmt -recursive .

py-fmt:
    {{uv_gh}} ruff format .github

validate:
    terraform init
    terraform validate
# === OK_EDIT: path-sync formatting ===

# === DO_NOT_EDIT: path-sync linting ===
# LINTING
lint:
    tflint -f compact --recursive --minimum-failure-severity=warning
    terraform fmt -check -recursive

py-check:
    {{uv_gh}} ruff format --exit-non-zero-on-format .github # avoids having to manually run `just py-fmt` after pre-commit check
    {{uv_gh}} ruff check .github

py-fix:
    {{uv_gh}} ruff check --fix .github
# === OK_EDIT: path-sync linting ===

# === DO_NOT_EDIT: path-sync testing-unit ===
# PYTHON TESTING
py-test:
    {{uv_gh}} pytest .github/ -v --ignore=.github/dev/

unit-plan-tests:
    terraform init
    terraform test {{PLAN_TEST_FILES}}
# === OK_EDIT: path-sync testing-unit ===

# === DO_NOT_EDIT: path-sync docs ===
# DOCUMENTATION
docs: fmt
    terraform-docs -c .terraform-docs.yml .
    @echo "Documentation generated successfully"
    {{py}} docs.generate_inputs_from_readme
    @echo "Inputs documentation updated successfully"
    just gen-readme
    @echo "Root README.md updated successfully"
    just gen-examples
    @echo "Examples README.md updated successfully"

check-docs:
    #!/usr/bin/env bash
    set -euo pipefail
    just docs
    if ! git diff --quiet; then
        echo "Documentation is out of date; the following files have uncommitted changes:" >&2
        git --no-pager diff --name-only >&2
        echo "Run 'just docs' locally and commit the changes to fix this failure." >&2
        exit 1
    fi
    echo "Documentation is up-to-date."

gen-readme *args:
    {{py}} docs.root_readme {{args}}

gen-examples *args:
    {{py}} docs.examples_readme {{args}}
    just fmt

gen-submodule-readme *args:
    {{py}} docs.submodule_readme {{args}}

md-link tag_version *args:
    {{py}} docs.md_link_absolute {{tag_version}} {{args}}

tf-registry-source:
    @{{py}} release.tf_registry_source
# === OK_EDIT: path-sync docs ===

# === DO_NOT_EDIT: path-sync changelog ===
# CHANGELOG
init-changelog:
    go install github.com/hashicorp/go-changelog/cmd/changelog-build@latest

build-changelog:
    {{py}} changelog.build_changelog

check-changelog-entry-file filepath:
    go run -C .github/changelog/check-changelog-entry-file . "{{justfile_directory()}}/{{filepath}}"

update-changelog-version version:
    {{py}} changelog.update_changelog_version {{version}}

generate-release-body version:
    @{{py}} changelog.generate_release_body {{version}}
# === OK_EDIT: path-sync changelog ===

# === DO_NOT_EDIT: path-sync release ===
# RELEASE
docs-release version:
    {{py}} release.update_version {{version}}
    @echo "Module versions updated successfully"
    just gen-examples --version {{version}}
    @echo "Examples README.md updated successfully"
    just gen-submodule-readme --version {{version}}
    @echo "Submodule README.md updated successfully"
    just gen-readme
    @echo "Root README.md updated successfully"
    just md-link {{version}}
    @echo "Markdown links converted to absolute URLs"
    just fmt

release-notes new_version old_version="":
    @{{py}} release.release_notes {{new_version}} {{old_version}}

check-release-ready version:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "Validating version {{version}}..."
    {{py}} release.validate_version {{version}}
    echo "Checking CHANGELOG.md is up-to-date..."
    just init-changelog
    just build-changelog
    if ! git diff --quiet CHANGELOG.md; then
        echo "Error: CHANGELOG.md is out of date"
        echo "Run 'just init-changelog && just build-changelog' and commit changes"
        git diff CHANGELOG.md
        exit 1
    fi
    echo "CHANGELOG.md is up-to-date"
    echo "Checking documentation is up-to-date..."
    just check-docs
    echo "All pre-release checks passed for {{version}}"

release-commit version:
    #!/usr/bin/env bash
    set -euo pipefail
    current_branch=$(git rev-parse --abbrev-ref HEAD)
    echo "Creating release {{version}} on branch=$current_branch..."
    just update-changelog-version {{version}}
    git add CHANGELOG.md
    git commit -m "chore: update CHANGELOG.md for {{version}}"
    just docs-release {{version}}
    git add .
    git commit -m "chore: release {{version}}"
    git tag {{version}}
    echo ""
    echo "Release {{version}} ready with tag"
    echo "Next steps:"
    echo "  1. git push origin {{version}}"
    echo "  2. just release-post-push"
    echo "  3. git push origin main"

release-post-push:
    git revert HEAD --no-edit
    @echo "Release commit reverted. Push main: git push origin main"
# === OK_EDIT: path-sync release ===

# === DO_NOT_EDIT: path-sync workspace ===
# WORKSPACE TESTING
ws-gen *args:
    {{py}} workspace.gen {{args}}

ws-plan *args:
    {{py}} workspace.plan {{args}}

ws-reg *args:
    {{py}} workspace.reg {{args}}

ws-run *args:
    {{py}} workspace.run {{args}}

ws-output-assertions *args:
    {{py}} workspace.output_assertions {{args}}

plan-only *args:
    just ws-run -m plan-only {{args}}

plan-snapshot-test *args:
    just ws-run -m plan-snapshot-test {{args}}

apply-examples *args:
    just ws-run -m apply {{args}}

check-outputs *args:
    just ws-run -m check-outputs {{args}}

destroy-examples *args:
    just ws-run -m destroy {{args}}
# === OK_EDIT: path-sync workspace ===

# === DO_NOT_EDIT: path-sync provider-dev ===
# PROVIDER DEV SETUP
setup-provider-dev provider_path:
    #!/usr/bin/env bash
    set -euo pipefail
    PROVIDER_ABS="$(cd "{{provider_path}}" && pwd)"
    PLUGIN_DIR="$PROVIDER_ABS/bin"
    cd "{{provider_path}}"
    echo "Building provider from source at $PROVIDER_ABS"
    make build
    echo "Creating dev.tfrc at {{justfile_directory()}}/dev.tfrc"
    uv run --directory "{{gh_dir}}" python -m dev.dev_vars tfrc "$PLUGIN_DIR" > "{{justfile_directory()}}/dev.tfrc"
    echo "Provider built at $PLUGIN_DIR"
    echo "Run: export TF_CLI_CONFIG_FILE=\"{{justfile_directory()}}/dev.tfrc\""
# === OK_EDIT: path-sync provider-dev ===

# === DO_NOT_EDIT: path-sync dev-vars-org ===
# DEV VARS - ORG (for modules that need org context)
dev-vars-org org_id:
    {{py}} dev.dev_vars org {{org_id}}
# === OK_EDIT: path-sync dev-vars-org ===

# === DO_NOT_EDIT: path-sync regions ===
# REGION EXTRACTION (for CSP modules with region mappings)
extract-regions provider *args: # use --output-dir to specify the output directory
    {{py}} dev.extract_regions --provider {{provider}} {{args}}

# validate-regions writes output to repo root and checks for drift (intended for destination repos, not cluster)
validate-regions provider *args:
    {{py}} dev.extract_regions --provider {{provider}} --fail-on-unmapped --output-dir {{justfile_directory()}} {{args}}
    git diff --exit-code --name-only {{justfile_directory()}} || (echo "Region files have uncommitted changes after extraction. Please commit the updated files." && exit 1)
# === OK_EDIT: path-sync regions ===

# === DO_NOT_EDIT: path-sync testing-tf ===
# TERRAFORM TESTING
tftest-all:
    terraform init
    terraform test -var 'org_id={{env_var("MONGODB_ATLAS_ORG_ID")}}'

test-compat:
    {{py}} dev.test_compat

update-terraform-versions:
    {{py}} dev.update_terraform_versions
# === OK_EDIT: path-sync testing-tf ===

# === DO_NOT_EDIT: path-sync sdlc-validate ===
# SDLC VALIDATION (only for destination repos)
sdlc-validate:
    uvx path-sync validate-no-changes -b main
# === OK_EDIT: path-sync sdlc-validate ===

# ---- Module-specific recipes (not synced) ----

dev-vars-project project_id:
    {{py}} dev.dev_vars project {{project_id}}

tf-gen *args:
    {{py}} tf_gen {{args}}

dev-integration-test:
    terraform init
    terraform test -filter=tests/apply_dev_cluster.tftest.hcl -var 'org_id={{env_var("MONGODB_ATLAS_ORG_ID")}}'

sdlc-sync-dry:
    uvx path-sync@latest copy -n sdlc --skip-commit --dry-run

sdlc-sync *args:
    uvx path-sync@latest copy -n sdlc --skip-commit {{args}}
