# Terraform Version Requirements

## Minimum Version: 1.10

This module requires **Terraform >= 1.10** to remain aligned with the [MongoDB Atlas Provider compatibility matrix](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs#hashicorp-terraform-version-compatibility-matrix).

## Why 1.10+ is Required

### Provider Support Policy

The MongoDB Atlas Provider supports Terraform versions that continue to receive security and maintenance updates. Terraform 1.10 is currently the oldest supported Terraform release.

### Cross-Variable Validation References

This module uses **cross-variable validation references** to provide a simpler and more intuitive user experience. These validations allow us to:

- Provide clear error messages when variables are misconfigured.
- Maintain validation logic that references multiple variables simultaneously, for example, validate `shard_count` against `cluster_type` to ensure they are compatible.

Cross-variable validation references establish a technical minimum of Terraform 1.9. The provider support policy raises the module's supported minimum to Terraform 1.10.

### Migration Path

If you're currently using Terraform 1.9 or earlier, you need to upgrade Terraform to use this module:

1. **Update Terraform**: Follow [HashiCorp's upgrade guide](https://developer.hashicorp.com/terraform/language/v1.10/upgrade-guide).
2. **Verify compatibility**: Run `terraform version` to confirm you're on 1.10 or later.
3. **Test your configuration**: Run `terraform init` and `terraform validate` to ensure everything works.

### Benefits of Upgrading

- **Supported Terraform release**: Receive current security and maintenance updates.
- **Better validation**: Get immediate feedback and clear error messages when variables are misconfigured.

## Version Compatibility Testing

This module is tested against all supported Terraform versions (1.10 and later). Run the compatibility tests locally:

```bash
just test-compat
```

The version matrix is defined in `.terraform-versions.yaml` and updated by the Terraform versions workflow.

## Related Documentation

- [Terraform 1.10 Upgrade Guide](https://developer.hashicorp.com/terraform/language/v1.10/upgrade-guide)
- [MongoDB Atlas Provider Compatibility Matrix](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs#hashicorp-terraform-version-compatibility-matrix)
- [Terraform Validation Blocks](https://developer.hashicorp.com/terraform/language/values/variables#custom-validation-rules)
