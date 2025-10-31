#!/usr/bin/env python
"""Compute Terraform Registry source from git repository information."""

import re
import subprocess
import sys


def get_git_remote_url() -> str:
    """Get the GitHub repository URL from git remote, preferring upstream over origin."""
    # Try origin first (for forks), then fall back to upstream to allow publishing from a fork
    for remote in ["origin", "upstream"]:
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", remote],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            continue

    raise subprocess.CalledProcessError(
        1, "git remote get-url", "No upstream or origin remote found"
    )


def parse_github_repo(remote_url: str) -> tuple[str, str]:
    """
    Parse GitHub repository owner and name from git remote URL.

    Returns:
        Tuple of (owner, repo_name)
    """
    # Handle both SSH and HTTPS URLs
    # SSH: git@github.com:mongodb/terraform-mongodbatlas-cluster.git
    # HTTPS: https://github.com/mongodb/terraform-mongodbatlas-cluster.git

    # Remove .git suffix if present
    remote_url = remote_url.removesuffix(".git")

    # Extract owner/repo from URL
    if remote_url.startswith("git@github.com:"):
        # SSH format
        path = remote_url.replace("git@github.com:", "")
    elif "github.com/" in remote_url:
        # HTTPS format
        path = remote_url.split("github.com/")[1]
    else:
        raise ValueError(f"Not a GitHub URL: {remote_url}")

    # Split into owner/repo
    parts = path.split("/")
    if len(parts) != 2:
        raise ValueError(f"Invalid GitHub repository path: {path}")

    return parts[0], parts[1]


def compute_registry_source(owner: str, repo_name: str) -> str:
    """
    Compute Terraform Registry source from repository name.

    Expected repository naming: terraform-{provider}-{module}
    Registry source format: terraform-{provider}-modules/{module}/{provider}

    Example:
        terraform-mongodbatlas-cluster -> terraform-mongodbatlas-modules/cluster/mongodbatlas
    """
    # Extract provider from repository name
    # Pattern: terraform-{provider}-{module}
    match = re.match(r"^terraform-([^-]+)-(.+)$", repo_name)

    if not match:
        raise ValueError(
            f"Repository name '{repo_name}' doesn't match expected pattern: terraform-{{provider}}-{{module}}"
        )

    provider = match.group(1)
    module_name = match.group(2)

    # Construct registry source
    registry_source = f"{owner}/{module_name}/{provider}"

    return registry_source


def main() -> None:
    """Main function."""
    try:
        # Get repository information from git
        remote_url = get_git_remote_url()
        owner, repo_name = parse_github_repo(remote_url)

        # Compute registry source
        registry_source = compute_registry_source(owner, repo_name)

        # Output only the registry source
        print(registry_source)

    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to get git remote: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
