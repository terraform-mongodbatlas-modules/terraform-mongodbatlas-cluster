"""HCL2 helpers for `versions.tf` using [python-hcl2](https://pypi.org/project/python-hcl2/)."""

from __future__ import annotations

from typing import Any, NamedTuple

from hcl2.api import loads

MONGODBATLAS_SOURCE = "mongodb/mongodbatlas"


class RequiredProviderEntry(NamedTuple):
    name: str
    version: str
    source: str | None


MODULE_VERSION_PATTERN = r'module_version\s*=\s*"[^"]*"'
"""Regex for `update_version` substitution on raw file text (avoids full round-trip via dumps)."""


def unwrap_hcl2_string(value: Any) -> str:
    """Normalize values from python-hcl2 (often wrapped in extra quote characters)."""
    if value is None:
        return ""
    if not isinstance(value, str):
        return str(value)
    s = value.strip()
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        return s[1:-1]
    return s


def iter_provider_entries(required_providers: list[Any]) -> list[RequiredProviderEntry]:
    """Collect provider pins from ``required_providers`` blocks."""
    out: list[RequiredProviderEntry] = []
    for block in required_providers:
        if not isinstance(block, dict):
            continue
        for name, body in block.items():
            if name in ("__is_block__", "__comments__") or not isinstance(body, dict):
                continue
            version_raw = body.get("version")
            source_raw = body.get("source")
            out.append(
                RequiredProviderEntry(
                    name=name,
                    version=unwrap_hcl2_string(version_raw) if version_raw is not None else "",
                    source=unwrap_hcl2_string(source_raw) if source_raw is not None else None,
                )
            )
    return out


def all_provider_entries(data: dict[str, Any]) -> list[RequiredProviderEntry]:
    acc: list[RequiredProviderEntry] = []
    for tb in data.get("terraform") or []:
        if not isinstance(tb, dict):
            continue
        acc.extend(iter_provider_entries(tb.get("required_providers") or []))
    return acc


def parse_versions_tf_dict(content: str) -> dict[str, Any] | None:
    """Parse HCL2; return None if parsing fails."""
    try:
        data = loads(content)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def terraform_required_version(terraform_blocks: list[Any]) -> str | None:
    if not terraform_blocks or not isinstance(terraform_blocks[0], dict):
        return None
    raw = terraform_blocks[0].get("required_version")
    if raw is None:
        return None
    return unwrap_hcl2_string(raw)


def find_mongodbatlas_provider_meta(terraform_blocks: list[Any]) -> dict[str, Any] | None:
    for tb in terraform_blocks:
        if not isinstance(tb, dict):
            continue
        for pm_block in tb.get("provider_meta") or []:
            if not isinstance(pm_block, dict):
                continue
            for key, inner in pm_block.items():
                if key in ("__is_block__", "__comments__") or not isinstance(inner, dict):
                    continue
                if key.strip('"') == "mongodbatlas":
                    return inner
    return None


def mongodbatlas_module_name_from_content(content: str) -> str | None:
    """Return `module_name` from `provider_meta \"mongodbatlas\"` if present."""
    data = parse_versions_tf_dict(content)
    if data is None:
        return None
    meta = find_mongodbatlas_provider_meta(data.get("terraform") or [])
    if meta is None:
        return None
    name = unwrap_hcl2_string(meta.get("module_name"))
    return name if name else None


def has_mongodbatlas_provider(content: str) -> bool:
    """True when `required_providers` declares mongodbatlas with the Atlas registry source."""
    data = parse_versions_tf_dict(content)
    if data is None:
        return False
    for entry in all_provider_entries(data):
        if entry.name == "mongodbatlas" and entry.source == MONGODBATLAS_SOURCE:
            return True
    return False


def has_provider_meta(content: str) -> bool:
    """True when a `provider_meta \"mongodbatlas\"` block exists."""
    data = parse_versions_tf_dict(content)
    if data is None:
        return False
    return find_mongodbatlas_provider_meta(data.get("terraform") or []) is not None
