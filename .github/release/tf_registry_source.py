"""Compute Terraform Registry source from git repository information."""

import re
import subprocess
import sys


def get_git_remote_url() -> str:
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
    remote_url = remote_url.removesuffix(".git")
    if remote_url.startswith("git@github.com:"):
        path = remote_url.replace("git@github.com:", "")
    elif "github.com/" in remote_url:
        path = remote_url.split("github.com/")[1]
    else:
        raise ValueError(f"Not a GitHub URL: {remote_url}")
    parts = path.split("/")
    if len(parts) != 2:
        raise ValueError(f"Invalid GitHub repository path: {path}")
    return parts[0], parts[1]


def compute_registry_source(owner: str, repo_name: str) -> str:
    match = re.match(r"^terraform-([^-]+)-(.+)$", repo_name)
    if not match:
        msg = f"Repository '{repo_name}' doesn't match pattern: terraform-{{provider}}-{{module}}"
        raise ValueError(msg)
    provider = match.group(1)
    module_name = match.group(2)
    registry_source = f"{owner}/{module_name}/{provider}"
    return registry_source


def get_github_repo_info() -> tuple[str, str, str]:
    remote_url = get_git_remote_url()
    owner, repo_name = parse_github_repo(remote_url)
    return f"https://github.com/{owner}/{repo_name}", owner, repo_name


def get_registry_source() -> str:
    remote_url = get_git_remote_url()
    owner, repo_name = parse_github_repo(remote_url)
    return compute_registry_source(owner, repo_name)


def main() -> None:
    try:
        remote_url = get_git_remote_url()
        owner, repo_name = parse_github_repo(remote_url)
        registry_source = compute_registry_source(owner, repo_name)
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
