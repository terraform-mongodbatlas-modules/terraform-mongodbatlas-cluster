"""Extract Atlas region mappings from listClusterProviderRegions API response.

Usage:
    MONGODB_ATLAS_PROJECT_ID=<project-id> uv run ./extract_regions.py
    MONGODB_ATLAS_PROJECT_ID=<project-id> uv run ./extract_regions.py --provider aws

Requires:
    - atlas CLI (authenticated)
    - aws CLI (authenticated, for AWS regions)
    - az CLI (authenticated, for Azure regions)
    - gcloud CLI (authenticated, for GCP regions)
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def fetch_atlas_regions(project_id: str) -> dict:
    """Fetch Atlas cluster provider regions using Atlas CLI.

    Args:
        project_id: MongoDB Atlas project ID (from MONGODB_ATLAS_PROJECT_ID env var)

    Returns:
        Raw API response dict from listClusterProviderRegions
    """
    try:
        result = subprocess.run(
            [
                "atlas",
                "api",
                "clusters",
                "listClusterProviderRegions",
                "--groupId",
                project_id,
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"  Atlas CLI error: {result.stderr.strip()}")
            return {}
        return json.loads(result.stdout)
    except FileNotFoundError:
        print("  Atlas CLI not found. Install with: brew install mongodb-atlas-cli")
        return {}
    except json.JSONDecodeError as e:
        print(f"  Failed to parse Atlas CLI response: {e}")
        return {}


def fetch_aws_regions() -> list[str]:
    """Fetch AWS regions using AWS CLI."""
    try:
        result = subprocess.run(
            [
                "aws",
                "ec2",
                "describe-regions",
                "--all-regions",
                "--region",
                "us-east-1",
                "--query",
                "Regions[].RegionName",
                "--output",
                "json",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"  AWS CLI error: {result.stderr.strip()}")
            return []
        return sorted(json.loads(result.stdout))
    except FileNotFoundError:
        print("  AWS CLI not found")
        return []


def fetch_azure_regions() -> list[str]:
    """Fetch Azure regions using Azure CLI."""
    try:
        result = subprocess.run(
            [
                "az",
                "account",
                "list-locations",
                "--query",
                "[].name",
                "--output",
                "json",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"  Azure CLI error: {result.stderr.strip()}")
            return []
        return sorted(json.loads(result.stdout))
    except FileNotFoundError:
        print("  Azure CLI not found")
        return []


def fetch_gcp_regions() -> list[str]:
    """Fetch GCP regions using gcloud CLI."""
    try:
        result = subprocess.run(
            ["gcloud", "compute", "regions", "list", "--format=json(name)"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"  GCP CLI error: {result.stderr.strip()}")
            return []
        data = json.loads(result.stdout)
        return sorted([r["name"] for r in data])
    except FileNotFoundError:
        print("  GCP CLI (gcloud) not found")
        return []


def load_or_fetch_provider_regions(
    output_dir: Path, provider_filter: str | None = None
) -> dict[str, list[str]]:
    """Load existing region files or fetch from CLIs.

    Args:
        output_dir: Directory to cache the provider region JSON files
        provider_filter: Optional provider to filter by (aws, azure, gcp)

    Returns:
        Dict mapping provider name (lowercase) to list of provider region names
    """
    all_providers = {
        "aws": fetch_aws_regions,
        "azure": fetch_azure_regions,
        "gcp": fetch_gcp_regions,
    }

    # Filter to specific provider if requested
    if provider_filter:
        provider_lower = provider_filter.lower()
        if provider_lower in all_providers:
            providers = {provider_lower: all_providers[provider_lower]}
        else:
            valid = ", ".join(all_providers.keys())
            sys.exit(f"Error: Invalid provider: {provider_filter}, valid: {valid}")
    else:
        providers = all_providers

    all_regions: dict[str, list[str]] = {}

    for provider, fetcher in providers.items():
        output_file = output_dir / f"{provider}_regions.json"

        # Try to load existing file first
        if output_file.exists():
            with open(output_file) as f:
                regions = json.load(f)
            if regions:
                print(
                    f"  {provider.upper()}: Loaded {len(regions)} regions from {output_file.name}"
                )
                all_regions[provider] = regions
                continue

        # Fetch from CLI
        print(f"  {provider.upper()}: Fetching from CLI...")
        regions = fetcher()
        all_regions[provider] = regions

        with open(output_file, "w") as f:
            json.dump(regions, f, indent=2)

        if regions:
            print(f"  {provider.upper()}: Written {len(regions)} regions to {output_file.name}")
        else:
            print(f"  {provider.upper()}: No regions fetched")

    return all_regions


def extract_atlas_regions(data: dict, provider_filter: str | None = None) -> dict[str, set[str]]:
    """Extract unique regions per provider from Atlas API response.

    Args:
        data: Raw API response from listClusterProviderRegions
        provider_filter: Optional provider to filter by (aws, azure, gcp)

    Returns:
        Dict mapping provider name (uppercase) to set of Atlas region names
    """
    provider_regions: dict[str, set[str]] = {}
    filter_upper = provider_filter.upper() if provider_filter else None

    for result in data.get("results", []):
        provider = result.get("provider")
        if not provider:
            continue

        # Skip if filtering and this isn't the requested provider
        if filter_upper and provider != filter_upper:
            continue

        if provider not in provider_regions:
            provider_regions[provider] = set()

        for instance_size in result.get("instanceSizes", []):
            for region in instance_size.get("availableRegions", []):
                region_name = region.get("name")
                if region_name:
                    provider_regions[provider].add(region_name)

    return provider_regions


# =============================================================================
# Static Region Mappings
# =============================================================================
# These are the authoritative Atlas -> Provider region mappings.
# Use None for Atlas regions that have no valid provider equivalent.

AZURE_REGION_MAP: dict[str, str] = {
    "ASIA_EAST": "eastasia",
    "ASIA_SOUTH_EAST": "southeastasia",
    "AUSTRALIA_CENTRAL": "australiacentral",
    "AUSTRALIA_CENTRAL_2": "australiacentral2",
    "AUSTRALIA_EAST": "australiaeast",
    "AUSTRALIA_SOUTH_EAST": "australiasoutheast",
    "BRAZIL_SOUTH": "brazilsouth",
    "BRAZIL_SOUTHEAST": "brazilsoutheast",
    "CANADA_CENTRAL": "canadacentral",
    "CANADA_EAST": "canadaeast",
    "CHILE_CENTRAL": "chilecentral",
    "EUROPE_NORTH": "northeurope",
    "EUROPE_WEST": "westeurope",
    "FRANCE_CENTRAL": "francecentral",
    "FRANCE_SOUTH": "francesouth",
    "GERMANY_NORTH": "germanynorth",
    "GERMANY_WEST_CENTRAL": "germanywestcentral",
    "INDIA_CENTRAL": "centralindia",
    "INDIA_SOUTH": "southindia",
    "INDIA_WEST": "westindia",
    "INDONESIA_CENTRAL": "indonesiacentral",
    "ISRAEL_CENTRAL": "israelcentral",
    "ITALY_NORTH": "italynorth",
    "JAPAN_EAST": "japaneast",
    "JAPAN_WEST": "japanwest",
    "KOREA_CENTRAL": "koreacentral",
    "KOREA_SOUTH": "koreasouth",
    "MALAYSIA_WEST": "malaysiawest",
    "MEXICO_CENTRAL": "mexicocentral",
    "NEW_ZEALAND_NORTH": "newzealandnorth",
    "NORWAY_EAST": "norwayeast",
    "NORWAY_WEST": "norwaywest",
    "POLAND_CENTRAL": "polandcentral",
    "QATAR_CENTRAL": "qatarcentral",
    "SOUTH_AFRICA_NORTH": "southafricanorth",
    "SOUTH_AFRICA_WEST": "southafricawest",
    "SPAIN_CENTRAL": "spaincentral",
    "SWEDEN_CENTRAL": "swedencentral",
    "SWEDEN_SOUTH": "swedensouth",
    "SWITZERLAND_NORTH": "switzerlandnorth",
    "SWITZERLAND_WEST": "switzerlandwest",
    "UAE_CENTRAL": "uaecentral",
    "UAE_NORTH": "uaenorth",
    "UK_SOUTH": "uksouth",
    "UK_WEST": "ukwest",
    "US_CENTRAL": "centralus",
    "US_EAST": "eastus",
    "US_EAST_2": "eastus2",
    "US_EAST_2_EUAP": "eastus2euap",
    "US_NORTH_CENTRAL": "northcentralus",
    "US_SOUTH_CENTRAL": "southcentralus",
    "US_WEST": "westus",
    "US_WEST_2": "westus2",
    "US_WEST_3": "westus3",
    "US_WEST_CENTRAL": "westcentralus",  # fmt: on
}

GCP_REGION_MAP: dict[str, str | None] = {
    "AFRICA_SOUTH_1": "africa-south1",
    "ASIA_EAST_2": "asia-east2",
    "ASIA_NORTHEAST_2": "asia-northeast2",
    "ASIA_NORTHEAST_3": "asia-northeast3",
    "ASIA_SOUTH_1": "asia-south1",
    "ASIA_SOUTH_2": "asia-south2",
    "ASIA_SOUTHEAST_2": "asia-southeast2",
    "AUSTRALIA_SOUTHEAST_1": "australia-southeast1",
    "AUSTRALIA_SOUTHEAST_2": "australia-southeast2",
    "EUROPE_CENTRAL_2": "europe-central2",
    "EUROPE_NORTH_1": "europe-north1",
    "EUROPE_SOUTHWEST_1": "europe-southwest1",
    "EUROPE_WEST_2": "europe-west2",
    "EUROPE_WEST_3": "europe-west3",
    "EUROPE_WEST_4": "europe-west4",
    "EUROPE_WEST_6": "europe-west6",
    "EUROPE_WEST_8": "europe-west8",
    "EUROPE_WEST_9": "europe-west9",
    "EUROPE_WEST_10": "europe-west10",
    "EUROPE_WEST_12": "europe-west12",
    "MIDDLE_EAST_CENTRAL_1": "me-central1",
    "MIDDLE_EAST_CENTRAL_2": "me-central2",
    "MIDDLE_EAST_WEST_1": "me-west1",
    "NORTH_AMERICA_NORTHEAST_1": "northamerica-northeast1",
    "NORTH_AMERICA_NORTHEAST_2": "northamerica-northeast2",
    "NORTH_AMERICA_SOUTH_1": "northamerica-south1",
    "SOUTH_AMERICA_EAST_1": "southamerica-east1",
    "SOUTH_AMERICA_WEST_1": "southamerica-west1",
    "US_EAST_4": "us-east4",
    "US_EAST_5": "us-east5",
    "US_SOUTH_1": "us-south1",
    "US_WEST_2": "us-west2",
    "US_WEST_3": "us-west3",
    "US_WEST_4": "us-west4",
    # Atlas geographic region aliases - mappings from:
    # https://www.mongodb.com/docs/atlas/reference/google-gcp/#stream-processing-workspaces
    "CENTRAL_US": "us-central1",  # Documented in Stream Processing Workspaces table
    "WESTERN_EUROPE": "europe-west1",  # Documented in Stream Processing Workspaces table
    # Inferred mappings based on GCP primary regions per geography:
    "EASTERN_US": "us-east1",  # Primary GCP east coast region
    "WESTERN_US": "us-west1",  # Primary GCP west coast region
    "EASTERN_ASIA_PACIFIC": "asia-east1",  # Taiwan (primary East Asia)
    "NORTHEASTERN_ASIA_PACIFIC": "asia-northeast1",  # Tokyo (primary Northeast Asia)
    "SOUTHEASTERN_ASIA_PACIFIC": "asia-southeast1",  # Singapore (primary Southeast Asia)
}


def atlas_to_aws(atlas_region: str) -> str:
    """Convert Atlas region to AWS region format.

    AWS has a consistent pattern: lowercase with hyphens.
    Example: US_EAST_1 -> us-east-1
    """
    return atlas_region.lower().replace("_", "-")


def create_validated_mappings(
    atlas_regions: dict[str, set[str]],
    provider_regions: dict[str, list[str]],
) -> dict[str, dict[str, dict]]:
    """Create Atlas -> Provider region mappings with validation.

    Uses static mappings for Azure and GCP, algorithmic for AWS.
    """
    mappings: dict[str, dict[str, dict]] = {}

    for provider, regions in sorted(atlas_regions.items()):
        provider_key = provider.lower()
        valid_regions = set(provider_regions.get(provider_key, []))

        mappings[provider] = {}
        for atlas_region in sorted(regions):
            # Use static mapping for Azure/GCP, algorithmic for AWS
            if provider == "AZURE":
                transformed = AZURE_REGION_MAP.get(atlas_region)
            elif provider == "GCP":
                transformed = GCP_REGION_MAP.get(atlas_region)
            else:  # AWS - algorithmic works perfectly
                transformed = atlas_to_aws(atlas_region)

            if transformed is None:
                # No mapping exists (legacy/unsupported region)
                mappings[provider][atlas_region] = {
                    "provider_region": None,
                    "valid": False,
                }
            else:
                is_valid = transformed in valid_regions
                mappings[provider][atlas_region] = {
                    "provider_region": transformed,
                    "valid": is_valid,
                }

    return mappings


def print_validation_summary(mappings: dict[str, dict[str, dict]]) -> None:
    """Print validation summary."""
    print("\n=== Validation Summary ===")

    for provider, regions in sorted(mappings.items()):
        valid_count = sum(1 for r in regions.values() if r["valid"])
        invalid_count = len(regions) - valid_count

        print(f"\n{provider}: {valid_count}/{len(regions)} valid")

        if invalid_count > 0:
            print("  Invalid mappings:")
            for atlas_region, info in sorted(regions.items()):
                if not info["valid"]:
                    provider_region = info["provider_region"]
                    if provider_region is None:
                        print(f"    {atlas_region} -> (NO MAPPING - legacy/unsupported)")
                    else:
                        print(f"    {atlas_region} -> {provider_region} (NOT FOUND)")


def generate_terraform_locals(
    provider: str,
    mappings: dict[str, dict],
    output_dir: Path,
    include_invalid: bool = False,
) -> Path:
    """Generate a regions.tf file with atlas<->provider region mappings.

    Args:
        provider: Provider name (aws, azure, gcp)
        mappings: Region mappings for the provider {atlas_region: {provider_region, valid}}
        output_dir: Directory to write the regions.tf file
        include_invalid: Whether to include invalid/unmapped regions (commented out)

    Returns:
        Path to the generated file
    """
    provider_lower = provider.lower()

    # Build the atlas_region_to_{provider} map
    lines = ["locals {"]
    lines.append(f"  atlas_region_to_{provider_lower} = {{")

    for atlas_region, info in sorted(mappings.items()):
        provider_region = info["provider_region"]
        is_valid = info["valid"]

        if provider_region is None:
            if include_invalid:
                lines.append(f"    # {atlas_region} = null  # No mapping exists")
            continue

        if is_valid:
            lines.append(f'    {atlas_region} = "{provider_region}"')
        elif include_invalid:
            lines.append(f'    # {atlas_region} = "{provider_region}"  # Not found in provider')

    lines.append("  }")
    lines.append("")

    # Add the reverse mapping
    lines.append(
        f"  {provider_lower}_region_to_atlas = "
        f"{{ for k, v in local.atlas_region_to_{provider_lower} : v => k }}"
    )
    lines.append("}")
    lines.append("")

    output_file = output_dir / f"regions_{provider_lower}.tf"
    with open(output_file, "w") as f:
        f.write("\n".join(lines))

    # Format with terraform fmt
    _run_terraform_fmt(output_file)

    return output_file


def _run_terraform_fmt(file_path: Path) -> None:
    """Run terraform fmt on a file."""
    subprocess.run(
        ["terraform", "fmt", str(file_path)],
        capture_output=True,
        text=True,
    )


def print_usage_snippet(provider: str) -> None:
    """Print Terraform usage snippet for region lookup."""
    p = provider.lower()
    provider_examples = {
        "aws": "us-east-1",
        "azure": "eastus",
        "gcp": "us-central1",
    }
    example = provider_examples.get(p, "region-name")
    snippet = f"""
# Usage: Add this to your module alongside the generated regions_{p}.tf

variable "region" {{
  type        = string
  description = "Atlas region (US_EAST_1) or {provider.upper()} region ({example})"
}}

locals {{
  # Normalize: always store as atlas region internally
  atlas_region = (
    contains(keys(local.atlas_region_to_{p}), var.region)
    ? var.region
    : lookup(local.{p}_region_to_atlas, var.region, null)
  )

  # Derive {provider.upper()} region from the normalized atlas region
  {p}_region = local.atlas_region != null ? local.atlas_region_to_{p}[local.atlas_region] : null

  region_error_message = local.atlas_region == null ? join("\\n", [
    "Unknown region: ${{var.region}}",
    "Valid Atlas regions: ${{join(", ", keys(local.atlas_region_to_{p}))}}",
    "Valid {provider.upper()} regions: ${{join(", ", keys(local.{p}_region_to_atlas))}}",
  ]) : null
}}

check "valid_region" {{
  assert {{
    condition     = local.region_error_message == null
    error_message = local.region_error_message
  }}
}}
"""
    print(snippet)


def load_or_fetch_atlas_regions(cache_dir: Path, project_id: str | None) -> dict:
    """Load existing Atlas regions file or fetch from Atlas CLI.

    Args:
        cache_dir: Directory to cache the regions.json file
        project_id: Atlas project ID (required if fetching from CLI)

    Returns:
        Raw API response dict from listClusterProviderRegions
    """
    output_file = cache_dir / "regions.json"

    # Try to load existing file first
    if output_file.exists():
        with open(output_file) as f:
            data = json.load(f)
        if data:
            print(f"  ATLAS: Loaded from {output_file.name}")
            return data

    # Fetch from CLI
    if not project_id:
        print("  ATLAS: No cached file and MONGODB_ATLAS_PROJECT_ID not set")
        print("  Set MONGODB_ATLAS_PROJECT_ID env var to fetch from Atlas CLI")
        return {}

    print(f"  ATLAS: Fetching from CLI (project: {project_id})...")
    data = fetch_atlas_regions(project_id)

    if data:
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)
        print(f"  ATLAS: Written to {output_file.name}")

    return data


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract Atlas region mappings from listClusterProviderRegions API"
    )
    parser.add_argument(
        "--provider",
        choices=["aws", "azure", "gcp"],
        help="Focus on a single provider and generate regions.tf",
    )
    parser.add_argument(
        "--include-invalid",
        action="store_true",
        help="Include invalid/unmapped regions as comments in regions.tf",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory for regions.tf (default: script directory)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    script_dir = Path(__file__).parent
    project_id = os.environ.get("MONGODB_ATLAS_PROJECT_ID")

    # Decode args at the beginning
    provider = args.provider  # None or "aws", "azure", "gcp"
    provider_upper = provider.upper() if provider else None
    include_invalid = args.include_invalid
    output_dir = args.output_dir or script_dir  # For .tf files only

    # Step 1: Load or fetch Atlas regions
    print("=== Step 1: Load/fetch Atlas regions ===")
    atlas_data = load_or_fetch_atlas_regions(script_dir, project_id)
    if not atlas_data:
        print("\nError: No Atlas regions data available.")
        print("Either provide regions.json or set MONGODB_ATLAS_PROJECT_ID env var.")
        return

    # Step 2: Load or fetch provider regions (JSON files go to script_dir)
    print("\n=== Step 2: Load/fetch provider regions ===")
    provider_regions = load_or_fetch_provider_regions(script_dir, provider)

    # Step 3: Extract Atlas regions from API response (filtered by provider if specified)
    print("\n=== Step 3: Extract Atlas regions ===")
    atlas_regions = extract_atlas_regions(atlas_data, provider)

    for prov, regions in sorted(atlas_regions.items()):
        print(f"  {prov}: {len(regions)} Atlas regions")

    # Step 4: Create and validate mappings
    print("\n=== Step 4: Create validated mappings ===")
    mappings = create_validated_mappings(atlas_regions, provider_regions)

    # Print validation summary
    print_validation_summary(mappings)

    # Step 5: Generate output
    if provider:
        # Single provider mode: generate regions.tf
        if provider_upper not in mappings:
            print(f"\nError: No mappings found for provider '{provider}'")
            return

        output_file = generate_terraform_locals(
            provider,
            mappings[provider_upper],
            output_dir,
            include_invalid=include_invalid,
        )
        print(f"\nGenerated {output_file}")
        print_usage_snippet(provider)
    else:
        # Default mode: write all mappings to JSON (to script_dir)
        output_file = script_dir / "region_mappings.json"
        with open(output_file, "w") as f:
            json.dump(mappings, f, indent=2)
        print(f"\nWritten to {output_file}")


if __name__ == "__main__":
    main()
