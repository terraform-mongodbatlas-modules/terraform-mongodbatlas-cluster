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
docs:
    terraform-docs -c .terraform-docs.yml .
    @echo "Documentation generated successfully"

# Run all validation checks
check: fmt validate lint docs
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

# Run all tests
test project-id:
    cd tests && terraform init
    cd tests && terraform test -var project_id={{project-id}}

# Run tests matching a file/path/pattern
test-filter project-id filter:
    cd tests && terraform init
    cd tests && terraform test -var project_id={{project-id}} -filter={{filter}}
