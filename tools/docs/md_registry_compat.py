"""Convert markdown files for Terraform Registry rendering.

The Terraform Registry serves the tagged README, so at release time the module
rewrites relative links to absolute GitHub URLs and GitHub alert blockquotes
(``> [!NOTE]``) to Registry callout markers (``->`` note, ``~>`` warning).
``main`` keeps the GitHub syntax, and ``release-post-push`` reverts the release
commit, so ``main`` renders on GitHub while the tag renders on the Registry.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_SKIP_FILES = [
    "CONTRIBUTING.md",
    "docs/example_readme.md",
]

ALERT_RE = r"^> \[!(?P<label>NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*$"

MARKERS = {
    "NOTE": "->",
    "TIP": "->",
    "IMPORTANT": "~>",
    "WARNING": "~>",
    "CAUTION": "~>",
}


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


def convert_admonitions_in_content(content: str) -> tuple[str, int, list[str]]:
    """Convert GitHub alert blockquotes to Terraform Registry callout markers.

    Returns the converted content, the number of admonitions converted, and the
    alert header lines left unchanged because their body could not be collapsed
    onto a single line: a multi-paragraph body, a nested blockquote body, or a
    missing body (all out of scope).
    """
    lines = content.split("\n")
    output: list[str] = []
    converted = 0
    skipped: list[str] = []
    index = 0
    while index < len(lines):
        match = re.match(ALERT_RE, lines[index])
        if match is None:
            output.append(lines[index])
            index += 1
            continue

        body_lines: list[str] = []
        next_index = index + 1
        while next_index < len(lines) and (
            lines[next_index].startswith("> ") or lines[next_index] == ">"
        ):
            body_lines.append(lines[next_index][2:] if lines[next_index].startswith("> ") else "")
            next_index += 1

        while body_lines and not body_lines[-1].strip():
            body_lines.pop()

        if not body_lines or any(not line.strip() or line.startswith(">") for line in body_lines):
            skipped.append(lines[index])
            output.append(lines[index])
            index += 1
            continue

        label = match.group("label")
        callout = f"{MARKERS[label]} **{label}:**"
        body = " ".join(body_lines).strip()
        if body:
            callout = f"{callout} {body}"
        output.append(callout)
        converted += 1
        index = next_index

    return "\n".join(output), converted, skipped


def process_markdown_file(
    md_file: Path,
    base_url: str,
    tag_version: str,
    root_dir: Path,
    dry_run: bool = False,
) -> tuple[bool, int, int, list[str]]:
    content = md_file.read_text(encoding="utf-8")
    original_content = content
    link_content = convert_links_in_content(content, md_file, base_url, tag_version, root_dir)
    new_content, admonitions_converted, skipped = convert_admonitions_in_content(link_content)
    if new_content == original_content:
        return False, 0, 0, skipped
    if not dry_run:
        md_file.write_text(new_content, encoding="utf-8")
    num_links = len(re.findall(r"\]\(" + re.escape(base_url), new_content)) - len(
        re.findall(r"\]\(" + re.escape(base_url), original_content)
    )
    return True, num_links, admonitions_converted, skipped


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Convert markdown files for Terraform Registry rendering: relative links to "
            "absolute GitHub URLs and GitHub alert blockquotes to Registry callout markers"
        )
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
    total_admonitions_converted = 0
    skipped_alerts: list[tuple[Path, str]] = []

    for md_file in md_files:
        was_modified, num_links, num_admonitions, skipped = process_markdown_file(
            md_file, github_url, tag_version, root_dir, dry_run=dry_run
        )
        rel_path = md_file.relative_to(root_dir)
        for alert in skipped:
            skipped_alerts.append((rel_path, alert))
        if was_modified:
            total_modified += 1
            total_links_converted += num_links
            total_admonitions_converted += num_admonitions
            prefix = "->" if dry_run else "ok"
            print(f"{prefix} {rel_path} ({num_links} links, {num_admonitions} admonitions)")

    print()
    for rel_path, alert in skipped_alerts:
        print(f"Warning: left multi-paragraph alert unchanged in {rel_path}: {alert}")
    action = "would be modified" if dry_run else "modified"
    total_converted = total_links_converted + total_admonitions_converted
    print(
        f"Summary: {total_modified} files {action}, "
        f"{total_links_converted} links and {total_admonitions_converted} admonitions "
        f"converted ({total_converted} total)"
    )


if __name__ == "__main__":
    main()
