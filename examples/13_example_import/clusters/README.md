# Generated Cluster Configurations

This directory contains auto-generated Terraform configurations for existing MongoDB Atlas clusters.

## Important: Achieving No Plan Changes Before Import

**Goal**: Before running `terraform apply` to import, you should iterate on these generated files until `terraform plan` shows **No changes**.

### Why This Matters

The import process will associate your existing Atlas clusters with these Terraform configurations. If the configuration doesn't exactly match your existing cluster:
- Terraform will try to modify your cluster on the next `terraform apply`
- You may experience unexpected changes to production clusters

### Iterative Process

1. **Run `terraform plan`** - Check what changes Terraform wants to make
2. **Adjust configuration** - Add or remove fields to match your existing cluster
3. **Repeat** until plan shows `No changes. Your infrastructure matches the configuration.`
4. **Then import** with `terraform apply`

### Common Adjustments Needed

The generator tries to omit default values, but you may need to:
- Add fields that were omitted but differ from module defaults
- Fine-tune auto-scaling settings

### After Import

Once imported successfully, run `terraform plan` one more time to verify no changes are detected.
