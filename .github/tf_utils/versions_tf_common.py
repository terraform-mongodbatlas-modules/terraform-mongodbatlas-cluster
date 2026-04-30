"""HCL2 helpers for `versions.tf` using [python-hcl2](https://pypi.org/project/python-hcl2/)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, NamedTuple

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


def provider_from_resource_type(type_str: str, root_provider_names: Iterable[str]) -> str | None:
    """Map a Terraform resource/data type string to a root provider name if it matches."""
    names = frozenset(root_provider_names)
    for p in sorted(names, key=len, reverse=True):
        if type_str == p or type_str.startswith(f"{p}_"):
            return p
    return None


def _resource_types_from_section(data: dict[str, Any], section: str) -> list[str]:
    out: list[str] = []
    for block in data.get(section) or []:
        if not isinstance(block, dict):
            continue
        for k in block:
            if k in ("__is_block__", "__comments__", "__inline_comments__"):
                continue
            out.append(unwrap_hcl2_string(k))
    return out


def providers_referenced_in_module_dir(
    module_dir: Path,
    root_provider_names: frozenset[str],
    *,
    for_versions_tf: Path | None = None,
) -> tuple[frozenset[str], list[str]]:
    """Collect root provider names referenced by resource/data blocks in ``*.tf`` (non-recursive).

    If ``for_versions_tf`` is set, that path is skipped so sibling usage is detected without
    re-parsing the file being validated (and without requiring resources in ``versions.tf``).

    Returns ``(used_root_providers, parse_errors)``. Parse errors are one line per failed file.
    """
    used: set[str] = set()
    errs: list[str] = []
    root_names = root_provider_names
    for tf_path in sorted(module_dir.glob("*.tf")):
        if for_versions_tf is not None and tf_path.resolve() == for_versions_tf.resolve():
            continue
        try:
            text = tf_path.read_text(encoding="utf-8")
            data = loads(text)
        except Exception as exc:
            errs.append(f"{tf_path}: HCL parse error: {exc}")
            continue
        if not isinstance(data, dict):
            errs.append(f"{tf_path}: unexpected parse result")
            continue
        for section in ("resource", "data"):
            for type_str in _resource_types_from_section(data, section):
                p = provider_from_resource_type(type_str, root_names)
                if p is not None:
                    used.add(p)
    return frozenset(used), errs
