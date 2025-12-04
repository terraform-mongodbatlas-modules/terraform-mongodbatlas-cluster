"""Terraform CLI version compatibility testing.

Runs `terraform init -backend=false` and `terraform validate` across all configured
Terraform versions (defined in .terraform-versions.yaml) for the root module and all examples.

Usage:
    uv run --with pyyaml python .github/test_compat.py
    # or via just:
    just test-compat

Note: For Terraform < 1.11, the root module is validated in a temp directory to avoid
parsing .tftest.hcl files that use features not available in older versions.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import yaml

# Terraform version that supports all test file features (state_key, etc.)
MIN_TFTEST_VERSION = (1, 11)


@dataclass
class TestResult:
    version: str
    target: str
    passed: bool
    output: str


def parse_version(version: str) -> tuple[int, ...]:
    """Parse version string into tuple for comparison."""
    return tuple(int(x) for x in version.split("."))


def load_versions(config_path: Path) -> list[str]:
    """Load Terraform versions from config file."""
    with config_path.open() as f:
        config = yaml.safe_load(f)
    return config["versions"]


def discover_targets(repo_root: Path) -> list[Path]:
    """Discover root module and all example directories."""
    targets = [repo_root]  # root module
    examples_dir = repo_root / "examples"
    if examples_dir.exists():
        for example in sorted(examples_dir.iterdir()):
            if example.is_dir() and (example / "main.tf").exists():
                targets.append(example)
    return targets


def copy_module_files(source: Path, dest: Path) -> None:
    """Copy only .tf files (not .tftest.hcl) for validation on older TF versions."""
    for tf_file in source.glob("*.tf"):
        shutil.copy2(tf_file, dest / tf_file.name)
    # Also copy modules/ directory if it exists (for submodules)
    modules_dir = source / "modules"
    if modules_dir.exists():
        shutil.copytree(modules_dir, dest / "modules")
    # Copy docs/ if referenced
    docs_dir = source / "docs"
    if docs_dir.exists():
        shutil.copytree(docs_dir, dest / "docs")


def run_validate(version: str, target: Path, use_temp_dir: bool = False) -> TestResult:
    """Run terraform init and validate for a specific version and target."""
    target_name = target.name if target.name != target.parent.name else "root"

    work_dir = target
    temp_dir_path = None

    if use_temp_dir:
        temp_dir_path = tempfile.mkdtemp(prefix=f"tf-compat-{target_name}-")
        work_dir = Path(temp_dir_path)
        copy_module_files(target, work_dir)

    try:
        # Run init
        init_cmd = [
            "mise",
            "x",
            f"terraform@{version}",
            "--",
            "terraform",
            "init",
            "-backend=false",
        ]
        init_result = subprocess.run(
            init_cmd,
            cwd=work_dir,
            capture_output=True,
            text=True,
        )
        if init_result.returncode != 0:
            return TestResult(
                version=version,
                target=target_name,
                passed=False,
                output=f"init failed:\n{init_result.stderr}",
            )

        # Run validate
        validate_cmd = [
            "mise",
            "x",
            f"terraform@{version}",
            "--",
            "terraform",
            "validate",
        ]
        validate_result = subprocess.run(
            validate_cmd,
            cwd=work_dir,
            capture_output=True,
            text=True,
        )

        if validate_result.returncode == 0:
            return TestResult(
                version=version, target=target_name, passed=True, output=""
            )

        return TestResult(
            version=version,
            target=target_name,
            passed=False,
            output=validate_result.stderr or validate_result.stdout,
        )
    finally:
        if temp_dir_path:
            shutil.rmtree(temp_dir_path, ignore_errors=True)


def print_summary(results: list[TestResult]) -> None:
    """Print summary table of results."""
    # Group by version
    versions = sorted(
        set(r.version for r in results), key=lambda v: [int(x) for x in v.split(".")]
    )

    print("\n" + "=" * 60)
    print("Terraform Version Compatibility Results")
    print("=" * 60)

    all_passed = True
    for version in versions:
        version_results = [r for r in results if r.version == version]
        passed = sum(1 for r in version_results if r.passed)
        total = len(version_results)
        status = "PASS" if passed == total else "FAIL"
        if status == "FAIL":
            all_passed = False
        print(f"  {version:8} : {status} ({passed}/{total} targets)")

    print("=" * 60)

    # Print failures
    failures = [r for r in results if not r.passed]
    if failures:
        print("\nFailures:\n")
        for r in failures:
            print(f"--- {r.version} / {r.target} ---")
            print(r.output.strip())
            print()

    if all_passed:
        print("\nAll versions passed validation.")
    else:
        print(f"\n{len(failures)} failure(s) detected.")


def main() -> int:
    repo_root = Path(__file__).parent.parent
    config_path = repo_root / ".terraform-versions.yaml"

    if not config_path.exists():
        print(f"Error: {config_path} not found", file=sys.stderr)
        return 1

    versions = load_versions(config_path)
    targets = discover_targets(repo_root)

    print(
        f"Testing {len(versions)} Terraform versions against {len(targets)} targets..."
    )
    print(f"Versions: {', '.join(versions)}")
    print(f"Targets: root + {len(targets) - 1} examples")
    print()

    results: list[TestResult] = []
    for version in versions:
        print(f"Testing Terraform {version}...", end=" ", flush=True)
        version_tuple = parse_version(version)
        # Use temp dir for root module on older TF versions to avoid parsing .tftest.hcl
        use_temp_for_root = version_tuple < MIN_TFTEST_VERSION

        version_passed = 0
        for target in targets:
            is_root = target == repo_root
            use_temp = use_temp_for_root and is_root
            result = run_validate(version, target, use_temp_dir=use_temp)
            results.append(result)
            if result.passed:
                version_passed += 1
        status = (
            "ok"
            if version_passed == len(targets)
            else f"{len(targets) - version_passed} failed"
        )
        print(status)

    print_summary(results)

    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
