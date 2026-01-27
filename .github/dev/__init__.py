"""Development utility scripts."""

from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
VERSIONS_FILE = REPO_ROOT / ".terraform-versions.yaml"
