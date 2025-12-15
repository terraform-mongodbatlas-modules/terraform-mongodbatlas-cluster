set dotenv-load

# List all commands
default:
    just --list

# Format all Terraform files
fmt:
    terraform fmt -recursive .

# Validate all Terraform files  
validate:
    terraform init
    terraform validate

# Lint with comprehensive rules
lint:
    tflint -f compact --recursive --minimum-failure-severity=warning
    terraform fmt -check -recursive

py-check:
    uv run --with ruff ruff check .github

py-fmt:
    uv run --with ruff ruff format .github

py-test:
    PYTHONPATH={{justfile_directory()}}/.github uv run --with pytest pytest .github/ -v --ignore=.github/test_compat.py

# Generate documentation
docs: fmt
    terraform-docs -c .terraform-docs.yml .
    @echo "Documentation generated successfully"
    uv run --with pyyaml python .github/generate_inputs_from_readme.py
    @echo "Inputs documentation updated successfully"
    just gen-readme
    @echo "Root README.md updated successfully"
    just gen-examples
    @echo "Examples README.md updated successfully"

# Run all validation checks
check: fmt validate lint check-docs py-check py-test
    @echo "All checks passed successfully"

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

# Run all integration tests (expects org_id env var)
integration-tests:
    terraform init
    terraform test -filter=tests/apply_dev_cluster.tftest.hcl -var 'org_id={{env_var("MONGODB_ATLAS_ORG_ID")}}'

# Run tests matching a file/path/pattern
unit-plan-tests:
    terraform init
    terraform test -filter=tests/plan_auto_scaling.tftest.hcl -filter=tests/plan_regions.tftest.hcl -filter=tests/plan_replication_spec.tftest.hcl

# Run all tests
test: unit-plan-tests integration-tests

# Generate workspace test files (variables.generated.tf, test_plan_snapshot.py)
ws-gen *args:
    PYTHONPATH={{justfile_directory()}}/.github uv run --with pyyaml --with typer python .github/tf_ws/gen.py {{args}}

# Run terraform plan for workspace tests
ws-plan *args:
    PYTHONPATH={{justfile_directory()}}/.github uv run --with pyyaml --with typer python .github/tf_ws/plan.py {{args}}

# Generate snapshot files and run pytest
ws-reg *args:
    PYTHONPATH={{justfile_directory()}}/.github uv run --with pyyaml --with typer --with pytest --with pytest-regressions python .github/tf_ws/reg.py {{args}}

# Run workspace test workflow (gen -> plan -> snapshot test)
ws-run *args:
    PYTHONPATH={{justfile_directory()}}/.github uv run --with pyyaml --with typer --with pytest --with pytest-regressions python .github/tf_ws/run.py {{args}}

# Convert relative markdown links to absolute GitHub URLs
md-link tag_version *args:
    uv run python .github/md_link_absolute.py {{tag_version}} {{args}}

# Generate README.md and versions.tf files for examples
gen-examples *args:
    PYTHONPATH={{justfile_directory()}}/.github uv run --with pyyaml python .github/examples_readme.py {{args}}
    just fmt

# Generate root README.md TOC and TABLES sections
gen-readme *args:
    PYTHONPATH={{justfile_directory()}}/.github uv run --with pyyaml python .github/root_readme.py {{args}}

# Show Terraform Registry source for this module
tf-registry-source:
    @uv run python .github/tf_registry_source.py

# Generate release notes for a version (requires commits on GitHub)
release-notes new_version old_version="":
    @uv run python .github/release_notes.py {{new_version}} {{old_version}}

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

# Run terraform validate across all supported Terraform versions
test-compat:
    uv run --with pyyaml python .github/test_compat.py

# Create release branch with version-specific documentation
release-commit version:
    @echo "Creating release {{version}}..."
    @uv run python .github/validate_version.py {{version}}
    git checkout -b {{version}}
    @uv run python .github/update_version.py {{version}}
    just gen-examples --version {{version}}
    just gen-readme
    just md-link {{version}}
    just fmt
    @echo "Committing changes..."
    git add .
    git commit -m "chore: release {{version}}"
    git tag {{version}}
    @echo ""
    @echo "✓ Release branch {{version}} ready with tag"
    @echo "  Review changes, then push:"
    @echo "  git push origin {{version}} --tags"

# Install go-changelog tool (required by build-changelog)
init-changelog:
    go install github.com/hashicorp/go-changelog/cmd/changelog-build@latest

# Update Unreleased section in CHANGELOG.md from .changelog/*.txt entries
build-changelog:
    uv run python .github/changelog/build_changelog.py

# Validate changelog entry file format
check-changelog-entry-file filepath:
    go run -C .github/changelog/check-changelog-entry-file . "{{justfile_directory()}}/{{filepath}}"

# Update CHANGELOG.md with version and current date
update-changelog-version version:
    uv run python .github/changelog/update_changelog_version.py {{version}}
