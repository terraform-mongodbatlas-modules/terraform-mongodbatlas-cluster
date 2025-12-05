# Terraform Version Requirements

## Minimum Version: 1.9

This module requires **Terraform >= 1.9**. This requirement is higher than the [MongoDB Atlas Provider's compatibility matrix](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs#hashicorp-terraform-version-compatibility-matrix), which supports Terraform 1.7.x and later.

## Why 1.9+ is Required

### Cross-Variable Validation References

This module uses **cross-variable validation references** to provide a simpler and more intuitive user experience. These validations allow us to:

- Provide clear error messages when variables are misconfigured
- Maintain validation logic that references multiple variables simultaneously for example Validate `shard_count` against `cluster_type` to ensure they're compatible

Cross-variable validation references are only supported in Terraform 1.9+. Terraform 1.6-1.8 do not support this feature.

### Migration Path

If you're currently using Terraform 1.6-1.8 with the MongoDB Atlas Provider, you'll need to upgrade Terraform to use this module. The upgrade process is straightforward:

1. **Update Terraform**: Follow [HashiCorp's upgrade guide](https://developer.hashicorp.com/terraform/language/v1.9/upgrade-guide)
2. **Verify compatibility**: Run `terraform version` to confirm you're on 1.9 or later
3. **Test your configuration**: Run `terraform init` and `terraform validate` to ensure everything works

### Benefits of Upgrading

- **Better validation**: Get immediate feedback on configuration errors
- **Improved user experience**: Clear error messages when variables are misconfigured
- **Future-proof**: Terraform 1.8 reaches EOL on 2026-04-30, so upgrading is recommended regardless

## Version Compatibility Testing

This module is tested against all supported Terraform versions (1.9 and later). Run the compatibility tests locally:

```bash
just test-compat
```

The version matrix is defined in `.terraform-versions.yaml`. Update this file when new Terraform versions are released.

## Related Documentation

- [Terraform 1.9 Upgrade Guide](https://developer.hashicorp.com/terraform/language/v1.9/upgrade-guide)
- [MongoDB Atlas Provider Compatibility Matrix](https://registry.terraform.io/providers/mongodb/mongodbatlas/latest/docs#hashicorp-terraform-version-compatibility-matrix)
- [Terraform Validation Blocks](https://developer.hashicorp.com/terraform/language/values/variables#custom-validation-rules)
