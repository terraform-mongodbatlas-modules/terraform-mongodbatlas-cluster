"""Terraform CLI version compatibility testing.

Runs `terraform init -backend=false` and `terraform validate` across all configured
Terraform versions (defined in .terraform-versions.yaml) for the root module and all examples.

Usage:
    uv run --directory .github python -m dev.test_compat
    # or via just:
    just test-compat
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import yaml

from dev import REPO_ROOT

MAX_WORKERS = min(os.cpu_count() or 4, 8)
INIT_MAX_RETRIES = 3
INIT_RETRY_DELAY_SECONDS = 10


@dataclass
class TestResult:
    version: str
    target: str
    passed: bool
    output: str


@dataclass
class TestJob:
    version: str
    target: Path
    use_temp_dir: bool


def load_versions(config_path: Path) -> list[str]:
    with config_path.open() as f:
        config = yaml.safe_load(f)
    return config["versions"]


def discover_targets() -> list[Path]:
    targets = [REPO_ROOT]
    examples_dir = REPO_ROOT / "examples"
    if examples_dir.exists():
        for example in sorted(examples_dir.iterdir()):
            if example.is_dir() and (example / "main.tf").exists():
                targets.append(example)
    return targets


def copy_module_files(source: Path, dest: Path) -> None:
    for tf_file in source.glob("*.tf"):
        shutil.copy2(tf_file, dest / tf_file.name)
    modules_dir = source / "modules"
    if modules_dir.exists():
        shutil.copytree(modules_dir, dest / "modules")


def run_validate(job: TestJob) -> TestResult:
    target_name = job.target.name if job.target.name != job.target.parent.name else "root"
    work_dir = job.target
    temp_dir_path = None

    if job.use_temp_dir:
        temp_dir_path = tempfile.mkdtemp(prefix=f"tf-compat-{target_name}-")
        work_dir = Path(temp_dir_path)
        copy_module_files(job.target, work_dir)

    try:
        init_cmd = [
            "mise",
            "x",
            f"terraform@{job.version}",
            "--",
            "terraform",
            "init",
            "-backend=false",
        ]
        init_result = None
        for attempt in range(1, INIT_MAX_RETRIES + 1):
            init_result = subprocess.run(init_cmd, cwd=work_dir, capture_output=True, text=True)
            if init_result.returncode == 0:
                break
            if attempt < INIT_MAX_RETRIES:
                time.sleep(INIT_RETRY_DELAY_SECONDS)

        if init_result.returncode != 0:
            return TestResult(
                version=job.version,
                target=target_name,
                passed=False,
                output=f"init failed after {INIT_MAX_RETRIES} attempts:\n{init_result.stderr}",
            )

        validate_cmd = ["mise", "x", f"terraform@{job.version}", "--", "terraform", "validate"]
        validate_result = subprocess.run(validate_cmd, cwd=work_dir, capture_output=True, text=True)

        if validate_result.returncode == 0:
            return TestResult(version=job.version, target=target_name, passed=True, output="")

        return TestResult(
            version=job.version,
            target=target_name,
            passed=False,
            output=validate_result.stderr or validate_result.stdout,
        )
    finally:
        if temp_dir_path:
            shutil.rmtree(temp_dir_path, ignore_errors=True)


def print_summary(results: list[TestResult]) -> None:
    versions = sorted(set(r.version for r in results), key=lambda v: [int(x) for x in v.split(".")])
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


def preinstall_versions(versions: list[str]) -> bool:
    print("Pre-installing Terraform versions...")
    for version in versions:
        print(f"  Installing terraform@{version}...", end=" ", flush=True)
        result = subprocess.run(
            ["mise", "install", f"terraform@{version}"], capture_output=True, text=True
        )
        if result.returncode != 0:
            print("FAIL")
            print(f"    Error: {result.stderr.strip()}", file=sys.stderr)
            return False
        print("ok")
    print()
    return True


def main() -> int:
    config_path = REPO_ROOT / ".terraform-versions.yaml"

    if not config_path.exists():
        print(f"Error: {config_path} not found", file=sys.stderr)
        return 1

    versions = load_versions(config_path)

    if not preinstall_versions(versions):
        return 1

    targets = discover_targets()

    jobs: list[TestJob] = []
    # Always use temp dirs for root module to avoid .terraform directory conflicts
    # when running multiple versions in parallel
    for version in versions:
        for target in targets:
            is_root = target == REPO_ROOT
            jobs.append(TestJob(version=version, target=target, use_temp_dir=is_root))

    total_jobs = len(jobs)
    print(f"Testing {len(versions)} Terraform versions against {len(targets)} targets...")
    print(f"Versions: {', '.join(versions)}")
    print(f"Targets: root + {len(targets) - 1} examples")
    print(f"Running {total_jobs} jobs with {MAX_WORKERS} workers...")
    print()

    results: list[TestResult] = []
    completed = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(run_validate, job): job for job in jobs}
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            completed += 1
            status = "ok" if result.passed else "FAIL"
            print(f"  [{completed}/{total_jobs}] {result.version} / {result.target}: {status}")

    print_summary(results)
    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
