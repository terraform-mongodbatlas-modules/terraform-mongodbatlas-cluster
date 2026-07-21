"""Convert relative links in markdown files to absolute GitHub URLs."""

import argparse
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_SKIP_FILES = [
    "CONTRIBUTING.md",
    "docs/example_readme.md",
]


def get_git_remote_url() -> str:
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
        check=True,
    )
    remote_url = result.stdout.strip()
    if remote_url.startswith("git@github.com:"):
        remote_url = remote_url.replace("git@github.com:", "https://github.com/")
    if remote_url.endswith(".git"):
        remote_url = remote_url[:-4]
    return remote_url


def validate_tag_version(tag: str) -> bool:
    pattern = r"^v\d+\.\d+\.\d+$"
    return bool(re.match(pattern, tag))


def find_markdown_files(root_dir: Path, skip_files: list[str]) -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "*.md", "**/*.md"],
            capture_output=True,
            text=True,
            check=True,
            cwd=root_dir,
        )
        md_files = []
        for line in result.stdout.strip().split("\n"):
            if line and line not in skip_files:
                md_files.append(root_dir / line)
        return md_files
    except subprocess.CalledProcessError:
        print("Warning: git ls-files failed, using glob (may include ignored files)")
        all_files = list(root_dir.glob("**/*.md"))
        return [f for f in all_files if str(f.relative_to(root_dir)) not in skip_files]


def resolve_relative_path(md_file: Path, relative_link: str, root_dir: Path) -> str:
    md_dir = md_file.parent
    target_path = (md_dir / relative_link).resolve()
    try:
        rel_from_root = target_path.relative_to(root_dir)
        return str(rel_from_root)
    except ValueError:
        return relative_link


def is_relative_link(link: str) -> bool:
    if not link:
        return False
    if link.startswith(("#", "http://", "https://", "mailto:", "ftp://")):
        return False
    return True


def convert_links_in_content(
    content: str, md_file: Path, base_url: str, tag_version: str, root_dir: Path
) -> str:
    link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"

    def replace_link(match: re.Match) -> str:
        link_text = match.group(1)
        link_url = match.group(2)
        if not is_relative_link(link_url):
            return match.group(0)
        absolute_path = resolve_relative_path(md_file, link_url, root_dir)
        github_url = f"{base_url}/blob/{tag_version}/{absolute_path}"
        return f"[{link_text}]({github_url})"

    return re.sub(link_pattern, replace_link, content)


def process_markdown_file(
    md_file: Path,
    base_url: str,
    tag_version: str,
    root_dir: Path,
    dry_run: bool = False,
) -> tuple[bool, int]:
    content = md_file.read_text(encoding="utf-8")
    original_content = content
    new_content = convert_links_in_content(content, md_file, base_url, tag_version, root_dir)
    if new_content != original_content:
        if not dry_run:
            md_file.write_text(new_content, encoding="utf-8")
        num_changes = len(re.findall(r"\]\(" + re.escape(base_url), new_content)) - len(
            re.findall(r"\]\(" + re.escape(base_url), original_content)
        )
        return True, num_changes
    return False, 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert relative links in markdown files to absolute GitHub URLs"
    )
    parser.add_argument("tag_version", help="Git tag version in format vX.Y.Z (e.g., v1.0.0)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without modifying")
    parser.add_argument("--no-skip", action="store_true", help="Process all files")
    args = parser.parse_args()

    tag_version = args.tag_version
    dry_run = args.dry_run
    skip_files = [] if args.no_skip else DEFAULT_SKIP_FILES

    if not validate_tag_version(tag_version):
        print(f"Error: tag_version must be in format vX.Y.Z, got: {tag_version}", file=sys.stderr)
        sys.exit(1)

    root_dir = Path.cwd()

    try:
        github_url = get_git_remote_url()
    except subprocess.CalledProcessError as e:
        print(f"Error getting git remote URL: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Repository: {github_url}")
    print(f"Tag version: {tag_version}")
    if dry_run:
        print("Mode: DRY RUN (no files will be modified)")
    if skip_files:
        print(f"Skipping files: {', '.join(skip_files)}")
    print()

    md_files = find_markdown_files(root_dir, skip_files)
    print(f"Found {len(md_files)} markdown files to process")
    print()

    total_modified = 0
    total_links_converted = 0

    for md_file in md_files:
        was_modified, num_links = process_markdown_file(
            md_file, github_url, tag_version, root_dir, dry_run=dry_run
        )
        if was_modified:
            total_modified += 1
            total_links_converted += num_links
            rel_path = md_file.relative_to(root_dir)
            prefix = "->" if dry_run else "ok"
            print(f"{prefix} {rel_path} ({num_links} converted)")

    print()
    action = "would be modified" if dry_run else "modified"
    print(f"Summary: {total_modified} files {action}, {total_links_converted} links converted")


if __name__ == "__main__":
    main()
