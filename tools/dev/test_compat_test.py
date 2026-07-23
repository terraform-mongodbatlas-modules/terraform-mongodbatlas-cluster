from pathlib import Path
from unittest.mock import MagicMock, patch

from dev.test_compat import TestJob as CompatJob
from dev.test_compat import TestResult as CompatResult
from dev.test_compat import run_validate

MODULE = run_validate.__module__


def test_run_validate_bypasses_lock_for_temp_dir():
    target_lock = MagicMock()
    job = CompatJob(
        version="1.15",
        target=Path("/repo"),
        use_temp_dir=True,
        target_lock=target_lock,
    )
    expected = CompatResult(version="1.15", target="root", passed=True, output="")

    with patch(f"{MODULE}._run_validate", return_value=expected) as mock_run:
        result = run_validate(job)

    assert result == expected
    mock_run.assert_called_once_with(job)
    target_lock.__enter__.assert_not_called()


def test_run_validate_locks_in_place_target():
    target_lock = MagicMock()
    job = CompatJob(
        version="1.15",
        target=Path("/repo/examples/example"),
        use_temp_dir=False,
        target_lock=target_lock,
    )
    expected = CompatResult(version="1.15", target="example", passed=True, output="")

    with patch(f"{MODULE}._run_validate", return_value=expected) as mock_run:
        result = run_validate(job)

    assert result == expected
    mock_run.assert_called_once_with(job)
    target_lock.__enter__.assert_called_once_with()
    target_lock.__exit__.assert_called_once()
