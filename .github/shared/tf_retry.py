from __future__ import annotations

import contextlib
import logging
import shutil
import subprocess
from pathlib import Path

from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

logger = logging.getLogger(__name__)

TRANSIENT_PATTERNS = [
    "does not match any of the checksums recorded in the dependency lock file",
    "Failed to query available provider packages",
    "Error while installing",
    "Could not retrieve the list of available versions",
    "registry service is unreachable",
]

CHECKSUM_PATTERN = "does not match any of the checksums recorded"


class TerraformInitError(RuntimeError):
    def __init__(self, stderr: str, work_dir: Path) -> None:
        self.stderr = stderr
        self.work_dir = work_dir
        super().__init__(f"terraform init failed in {work_dir}: {stderr[:200]}")


def _is_transient(error: BaseException) -> bool:
    if not isinstance(error, TerraformInitError):
        return False
    return any(p in error.stderr for p in TRANSIENT_PATTERNS)


def _cleanup_terraform_cache(work_dir: Path) -> None:
    for subdir in (".terraform/providers", ".terraform/modules"):
        path = work_dir / subdir
        if path.exists():
            logger.info(f"removing stale cache: {path}")
            with contextlib.suppress(FileNotFoundError):
                shutil.rmtree(path)


def _log_retry(state: RetryCallState) -> None:
    exc = state.outcome.exception() if state.outcome else None
    work_dir = exc.work_dir if isinstance(exc, TerraformInitError) else "?"
    logger.warning(f"terraform init retry #{state.attempt_number} in {work_dir}")


def _before_retry(state: RetryCallState) -> None:
    exc = state.outcome.exception() if state.outcome else None
    if isinstance(exc, TerraformInitError) and CHECKSUM_PATTERN in exc.stderr:
        _cleanup_terraform_cache(exc.work_dir)
    _log_retry(state)


@retry(
    retry=retry_if_exception(_is_transient),
    stop=stop_after_attempt(4),
    wait=wait_exponential_jitter(initial=5, max=60, jitter=5),
    before_sleep=_before_retry,
    reraise=True,
)
def run_terraform_init(cmd: list[str], work_dir: Path) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, cwd=work_dir, capture_output=True, text=True)
    if result.returncode != 0:
        raise TerraformInitError(result.stderr, work_dir)
    return result
