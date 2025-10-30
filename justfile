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

# Generate documentation
docs: gen-readme gen-examples
    terraform-docs -c .terraform-docs.yml .
    @echo "Documentation generated successfully"

# Run all validation checks
check: fmt validate lint check-docs
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
    terraform test -filter=tests/apply_regions.tftest.hcl -var 'org_id={{env_var("MONGODB_ATLAS_ORG_ID")}}'

# Run tests matching a file/path/pattern
unit-plan-tests:
    terraform init
    terraform test -filter=tests/plan_auto_scaling.tftest.hcl -filter=tests/plan_regions.tftest.hcl -filter=tests/plan_replication_spec.tftest.hcl

# Run all tests
test: unit-plan-tests integration-tests

# Convert relative markdown links to absolute GitHub URLs
md-link tag_version *args:
    uv run python .github/md_link_absolute.py {{tag_version}} {{args}}

# Generate README.md and versions.tf files for examples
gen-examples *args:
    uv run --with pyyaml python .github/examples_readme.py {{args}}
    just fmt

# Generate root README.md TOC and TABLES sections
gen-readme *args:
    uv run --with pyyaml python .github/root_readme.py {{args}}

# Show Terraform Registry source for this module
tf-registry-source:
    @uv run python .github/tf_registry_source.py

# Generate release notes for a version (requires commits on GitHub)
release-notes new_version old_version="":
    @uv run python .github/release_notes.py {{new_version}} {{old_version}}

# Check if documentation is up-to-date (for CI)
check-docs:
    uv run --with pyyaml python .github/root_readme.py --check
    uv run --with pyyaml python .github/examples_readme.py --check

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
    git add .
    git commit -m "chore: release {{version}}"
    git tag {{version}}
    @echo ""
    @echo "✓ Release branch {{version}} ready with tag"
    @echo "  Review changes, then push:"
    @echo "  git push origin {{version}} --tags"
