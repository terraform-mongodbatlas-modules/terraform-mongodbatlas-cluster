from __future__ import annotations

import logging
import subprocess
from tempfile import NamedTemporaryFile

logger = logging.getLogger(__name__)


def render_description(desc: str) -> str:
    if "\n" in desc:
        return f"<<-EOT\n{desc}\nEOT"
    escaped = desc.replace('"', '\\"')
    return f'"{escaped}"'


def format_terraform(content: str) -> str:
    try:
        with NamedTemporaryFile(mode="w", suffix=".tf", delete=False) as f:
            f.write(content)
            f.flush()
            subprocess.run(
                ["terraform", "fmt", f.name], check=True, capture_output=True
            )
            return open(f.name).read()
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("terraform fmt unavailable, returning unformatted")
        return content
