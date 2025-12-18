"""Configuration for active resources and provider versions used in schema tests."""

from __future__ import annotations

from dataclasses import dataclass

# Provider sources and versions
PROVIDER_VERSIONS: dict[str, str] = {
    "mongodb/mongodbatlas": "~> 2.2",
    "hashicorp/aws": "~> 5.0",
}


@dataclass
class ResourceConfig:
    """Configuration for a resource schema test."""

    provider_source: str
    resource_type: (
        str  # without provider prefix, e.g., "project" not "mongodbatlas_project"
    )

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
    ResourceConfig("mongodb/mongodbatlas", "project"),
    ResourceConfig("mongodb/mongodbatlas", "advanced_cluster"),
    ResourceConfig("mongodb/mongodbatlas", "cloud_backup_schedule"),
    ResourceConfig("mongodb/mongodbatlas", "database_user"),
    # AWS resources
    ResourceConfig("hashicorp/aws", "vpc_endpoint"),
]


def resources_by_provider() -> dict[str, list[ResourceConfig]]:
    """Group active resources by provider source."""
    result: dict[str, list[ResourceConfig]] = {}
    for rc in ACTIVE_RESOURCES:
        result.setdefault(rc.provider_source, []).append(rc)
    return result
