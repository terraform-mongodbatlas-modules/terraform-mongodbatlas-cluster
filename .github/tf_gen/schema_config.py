"""Configuration for active resources and provider versions used in schema tests."""

from __future__ import annotations

from dataclasses import dataclass

MONGODB_ATLAS_PROVIDER_SOURCE = "mongodb/mongodbatlas"
AWS_PROVIDER_SOURCE = "hashicorp/aws"

# Provider sources and versions
PROVIDER_VERSIONS: dict[str, str] = {
    MONGODB_ATLAS_PROVIDER_SOURCE: "~> 2.2",
    AWS_PROVIDER_SOURCE: "~> 5.0",
}


@dataclass
class ResourceConfig:
    """Configuration for a resource schema test."""

    provider_source: str
    resource_type: str  # without provider prefix, e.g., "project" not "mongodbatlas_project"

    @property
    def provider_name(self) -> str:
        """Extract provider name from source, e.g., 'mongodb/mongodbatlas' -> 'mongodbatlas'."""
        return self.provider_source.split("/")[-1]

    @property
    def full_resource_type(self) -> str:
        """Full resource type with provider prefix."""
        return f"{self.provider_name}_{self.resource_type}"

    @property
    def schema_filename(self) -> str:
        """Filename for the schema JSON file."""
        return f"{self.full_resource_type}.json"


# Active resources to download and test
ACTIVE_RESOURCES: list[ResourceConfig] = [
    # MongoDB Atlas resources
    ResourceConfig(MONGODB_ATLAS_PROVIDER_SOURCE, "project"),
    ResourceConfig(MONGODB_ATLAS_PROVIDER_SOURCE, "advanced_cluster"),
    ResourceConfig(MONGODB_ATLAS_PROVIDER_SOURCE, "cloud_backup_schedule"),
    ResourceConfig(MONGODB_ATLAS_PROVIDER_SOURCE, "database_user"),
    ResourceConfig(MONGODB_ATLAS_PROVIDER_SOURCE, "federated_database_instance"),
    ResourceConfig(MONGODB_ATLAS_PROVIDER_SOURCE, "cloud_provider_access_setup"),
    ResourceConfig(MONGODB_ATLAS_PROVIDER_SOURCE, "cloud_provider_access_authorization"),
    # AWS resources
    ResourceConfig(AWS_PROVIDER_SOURCE, "vpc_endpoint"),
]


def resources_by_provider() -> dict[str, list[ResourceConfig]]:
    """Group active resources by provider source."""
    result: dict[str, list[ResourceConfig]] = {}
    for rc in ACTIVE_RESOURCES:
        result.setdefault(rc.provider_source, []).append(rc)
    return result
