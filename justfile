set dotenv-load

# =============================================================================
# Default
# =============================================================================

# List all commands
default:
    just --list

# =============================================================================
# Pre-commit / Pre-push
# =============================================================================

# Run fast checks (suitable for pre-commit hooks)
pre-commit: fmt validate lint check-docs py-check
    @echo "Pre-commit checks passed"

# Run slower checks (suitable for pre-push hooks)
pre-push: pre-commit unit-plan-tests py-test
    @echo "Pre-push checks passed"

# =============================================================================
# Dev Setup
# =============================================================================

# Sync Python dependencies
uv-sync:
    uv sync --directory .github

# Generate dev.tfvars with a project_id (reused for all 5 project slots)
dev-vars-project project_id:
    uv run --directory .github python -m dev.dev_vars project {{project_id}}

# Generate dev.tfvars with an org_id (projects created dynamically)
dev-vars-org org_id:
    uv run --directory .github python -m dev.dev_vars org {{org_id}}

# Build provider from source and create dev.tfrc for dev_overrides
setup-provider-dev provider_path:
    #!/usr/bin/env bash
    set -euo pipefail
    PROVIDER_ABS="$(cd "{{provider_path}}" && pwd)"
    PLUGIN_DIR="$PROVIDER_ABS/bin"
    cd "{{provider_path}}"
    echo "Building provider from source at $PROVIDER_ABS"
    make build
    echo "Creating dev.tfrc at {{justfile_directory()}}/dev.tfrc"
    cat > "{{justfile_directory()}}/dev.tfrc" <<EOF
    provider_installation {
      dev_overrides {
        "mongodb/mongodbatlas" = "$PLUGIN_DIR"
      }
      direct {}
    }
    EOF
    echo "Provider built at $PLUGIN_DIR"
    echo "Run: export TF_CLI_CONFIG_FILE=\"{{justfile_directory()}}/dev.tfrc\""

# =============================================================================
# Formatting
# =============================================================================

# Format all Terraform files
fmt:
    terraform fmt -recursive .

# Format Python code
py-fmt:
    uv run --directory .github ruff format .github

# Validate all Terraform files
validate:
    terraform init
    terraform validate

# =============================================================================
# Linting
# =============================================================================

# Lint with comprehensive rules
lint:
    tflint -f compact --recursive --minimum-failure-severity=warning
    terraform fmt -check -recursive

# Lint Python code
py-check:
    uv run --directory .github ruff check .github

# =============================================================================
# Testing
# =============================================================================

# Run Python unit tests
py-test:
    uv run --directory .github pytest .github/ -v --ignore=.github/dev/test_compat.py

# Run Terraform unit plan tests
unit-plan-tests:
    terraform init
    terraform test -filter=tests/plan_auto_scaling.tftest.hcl -filter=tests/plan_regions.tftest.hcl -filter=tests/plan_replication_spec.tftest.hcl -filter=tests/plan_geosharded_multi_shard.tftest.hcl -filter=tests/plan_sharded.tftest.hcl

# Run dev cluster integration test (fast, single cluster apply/destroy)
dev-integration-test:
    terraform init
    terraform test -filter=tests/apply_dev_cluster.tftest.hcl -var 'org_id={{env_var("MONGODB_ATLAS_ORG_ID")}}'

# Run all terraform tests (plan + apply tests, no filter)
tftest-all:
    terraform init
    terraform test -var 'org_id={{env_var("MONGODB_ATLAS_ORG_ID")}}'

# Run terraform validate across all supported Terraform versions
test-compat:
    uv run --directory .github python -m dev.test_compat

# =============================================================================
# Documentation
# =============================================================================

# Generate documentation
docs: fmt
    terraform-docs -c .terraform-docs.yml .
    @echo "Documentation generated successfully"
    uv run --directory .github python -m docs.generate_inputs_from_readme
    @echo "Inputs documentation updated successfully"
    just gen-readme
    @echo "Root README.md updated successfully"
    just gen-examples
    @echo "Examples README.md updated successfully"

# Check if documentation is up-to-date (for CI)
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

# Generate root README.md TOC and TABLES sections
gen-readme *args:
    uv run --directory .github python -m docs.root_readme {{args}}

# Generate README.md and versions.tf files for examples
gen-examples *args:
    uv run --directory .github python -m docs.examples_readme {{args}}
    just fmt

# Generate submodule README.md files with registry source
gen-submodule-readme *args:
    uv run --directory .github python -m docs.submodule_readme {{args}}

# Convert relative markdown links to absolute GitHub URLs
md-link tag_version *args:
    uv run --directory .github python -m docs.md_link_absolute {{tag_version}} {{args}}

# Show Terraform Registry source for this module
tf-registry-source:
    @uv run --directory .github python -m release.tf_registry_source

# =============================================================================
# Workspace Testing
# =============================================================================

# Generate workspace test files (variables.generated.tf, test_plan_snapshot.py)
ws-gen *args:
    uv run --directory .github python -m workspace.gen {{args}}

# Run terraform plan for workspace tests
ws-plan *args:
    uv run --directory .github python -m workspace.plan {{args}}

# Generate snapshot files and run pytest
ws-reg *args:
    uv run --directory .github python -m workspace.reg {{args}}

# Run workspace test workflow gen -> plan -> snapshot test -> apply
ws-run *args:
    uv run --directory .github python -m workspace.run {{args}}

# Runs workspace generation and terraform plan
plan-only *args:
    just ws-run -m plan-only {{args}}

# Runs workspace generation, terraform plan, and snapshot test
plan-snapshot-test *args:
    just ws-run -m plan-snapshot-test {{args}}

# Runs workspace generation and terraform apply
apply-examples *args:
    just ws-run -m apply {{args}}

# Runs workspace generation and terraform destroy
destroy-examples *args:
    just ws-run -m destroy {{args}}

# =============================================================================
# Examples
# =============================================================================

# Initialize examples
init-examples:
    #!/bin/bash
    set -euo pipefail
    for example in examples/*/; do
        echo "Initializing $example"
        (cd "$example" && terraform init -upgrade)
    done

# Plan all examples (dry run)
plan-examples project_id:
    #!/bin/bash
    set -euo pipefail
    for example in examples/*/; do
        echo "Planning $example"
        (cd "$example" && terraform plan -var project_id={{project_id}} -var-file=../tags.tfvars )
    done

# =============================================================================
# Changelog
# =============================================================================

# Install go-changelog tool (required by build-changelog)
init-changelog:
    go install github.com/hashicorp/go-changelog/cmd/changelog-build@latest

# Update Unreleased section in CHANGELOG.md from .changelog/*.txt entries
build-changelog:
    uv run --directory .github python -m changelog.build_changelog

# Validate changelog entry file format
check-changelog-entry-file filepath:
    go run -C .github/changelog/check-changelog-entry-file . "{{justfile_directory()}}/{{filepath}}"

# Update CHANGELOG.md with version and current date
update-changelog-version version:
    uv run --directory .github python -m changelog.update_changelog_version {{version}}

# Generate GitHub release body from CHANGELOG.md
generate-release-body version:
    @uv run --directory .github python -m changelog.generate_release_body {{version}}

# =============================================================================
# Release
# =============================================================================

# Generate all release-specific updates (versions, docs, links)
docs-release version:
    uv run --directory .github python -m release.update_version {{version}}
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

# Generate release notes for a version (requires commits on GitHub)
release-notes new_version old_version="":
    @uv run --directory .github python -m release.release_notes {{new_version}} {{old_version}}

# Validate release prerequisites (used locally and by GHA)
check-release-ready version:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "Validating version {{version}}..."
    uv run --directory .github python -m release.validate_version {{version}}
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

# Create release on main branch with changelog and release commits
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

# Revert the release commit after pushing the tag
release-post-push:
    git revert HEAD --no-edit
    @echo "Release commit reverted. Push main: git push origin main"
