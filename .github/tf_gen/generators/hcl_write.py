from __future__ import annotations

import logging
import subprocess
from collections.abc import Callable
from tempfile import NamedTemporaryFile
from typing import TypeVar

logger = logging.getLogger(__name__)

DEPRECATED_NAME = "DEPRECATED"
DEPRECATED_PREFIX = f"{DEPRECATED_NAME}: "


def make_description(
    description: str | None,
    deprecated: bool,
    deprecated_message: str | None = None,
) -> str | None:
    if not deprecated:
        return description
    if deprecated_message:
        return f"{DEPRECATED_PREFIX}{deprecated_message}"
    if description:
        return f"{DEPRECATED_PREFIX}{description}"
    return DEPRECATED_NAME


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
            subprocess.run(["terraform", "fmt", f.name], check=True, capture_output=True)
            return open(f.name).read()
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("terraform fmt unavailable, returning unformatted")
        return content


T = TypeVar("T")


def render_blocks(specs: list[T], render_fn: Callable[[T], str]) -> str:
    content = "\n\n".join(render_fn(s) for s in specs)
    return format_terraform(content)
