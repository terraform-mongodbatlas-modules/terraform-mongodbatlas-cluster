"""Generate release notes by comparing current version with previous release."""

import subprocess
import sys


def get_previous_tag(current_version: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "tag", "-l", "v*.*.*"],
            capture_output=True,
            text=True,
            check=True,
        )
        tags = [
            tag.strip()
            for tag in result.stdout.strip().split("\n")
            if tag.strip() and tag.strip() != current_version
        ]
        if not tags:
            return None
        sorted_tags = sorted(tags, key=lambda t: [int(x) for x in t.lstrip("v").split(".")])
        return sorted_tags[-1] if sorted_tags else None
    except (subprocess.CalledProcessError, ValueError):
        return None


def get_merge_base(ref: str, base: str = "main") -> str | None:
    try:
        result = subprocess.run(
            ["git", "merge-base", ref, base],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def generate_notes_from_git_log(from_ref: str, to_ref: str) -> str:
    try:
        from_base = get_merge_base(from_ref, "main")
        to_base = get_merge_base(to_ref, "main")
        if from_base and to_base and from_base != to_base:
            print(f"Comparing main commits: {from_base[:8]}..{to_base[:8]}", file=sys.stderr)
            compare_from = from_base
            compare_to = to_base
        else:
            compare_from = from_ref
            compare_to = to_ref
        result = subprocess.run(
            [
                "git",
                "log",
                f"{compare_from}..{compare_to}",
                "--pretty=format:* %s (%h)",
                "--no-merges",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        commits = result.stdout.strip()
        if not commits:
            return f"No changes found between {from_ref} and {to_ref}."
        notes = "## What's Changed\n\n"
        notes += commits + "\n\n"
        notes += f"**Full Changelog**: {compare_from}...{compare_to}\n"
        return notes
    except subprocess.CalledProcessError as e:
        print(f"Error generating notes from git log: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: release_notes.py <new_version> [old_version]", file=sys.stderr)
        print("", file=sys.stderr)
        print("Examples:", file=sys.stderr)
        print(
            "  release_notes.py v1.0.0              # Auto-detect previous release", file=sys.stderr
        )
        print("  release_notes.py v1.1.0 v1.0.0       # Compare specific versions", file=sys.stderr)
        print(
            "  release_notes.py v1.0.0 abc123       # Compare with specific commit", file=sys.stderr
        )
        sys.exit(1)

    current_version = sys.argv[1]
    old_version = sys.argv[2] if len(sys.argv) == 3 else None
    print(f"Generating release notes for {current_version}...", file=sys.stderr)

    if old_version:
        print(f"Using specified previous version: {old_version}", file=sys.stderr)
        previous_ref = old_version
    else:
        previous_ref = get_previous_tag(current_version)
        if not previous_ref:
            print("No previous release found - this is the first release", file=sys.stderr)
            print("", file=sys.stderr)
            print("Tip: Specify a commit/tag to compare against:", file=sys.stderr)
            print(f"     just release-notes {current_version} <previous_commit>", file=sys.stderr)
            print("Initial release of terraform-mongodbatlas-cluster module.")
            return

    print(f"Comparing {previous_ref} -> {current_version}", file=sys.stderr)
    notes = generate_notes_from_git_log(previous_ref, current_version)
    print(notes)


if __name__ == "__main__":
    main()
