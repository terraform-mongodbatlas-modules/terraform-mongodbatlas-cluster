"""Validate examples and submodule versions.tf files against the repo root `versions.tf`.

Uses [python-hcl2](https://pypi.org/project/python-hcl2/) via `hcl2.api.loads` for HCL2 parsing.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import typer
from hcl2.api import loads

from tf_utils.versions_tf_common import (
    all_provider_entries,
    providers_referenced_in_module_dir,
    terraform_required_version,
)


@dataclass(frozen=True)
class RootVersionsRef:
    """Pins from the repository root `versions.tf` terraform block."""

    providers: dict[str, tuple[str, str | None]]
    required_version: str | None


def parse_root_versions_reference(repo_root: Path) -> RootVersionsRef:
    """Load pins from ``repo_root / versions.tf``."""
    root_file = repo_root / "versions.tf"
    if not root_file.is_file():
        raise FileNotFoundError(f"{root_file}: root versions.tf not found")

    data = loads(root_file.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{root_file}: unexpected parse result")

    terraform_blocks = data.get("terraform") or []
    if not terraform_blocks or not isinstance(terraform_blocks[0], dict):
        raise ValueError(f"{root_file}: no terraform block")

    providers_list = all_provider_entries(data)
    if not providers_list:
        raise ValueError(f"{root_file}: missing or empty required_providers")

    providers = {e.name: (e.version, e.source) for e in providers_list}
    rv = terraform_required_version(terraform_blocks)

    return RootVersionsRef(providers=providers, required_version=rv)


def _errors_for_file(path: Path, content: str, root: RootVersionsRef) -> list[str]:
    errs: list[str] = []
    root_names = frozenset(root.providers.keys())
    used, scan_errs = providers_referenced_in_module_dir(
        path.parent, root_names, for_versions_tf=path
    )
    errs.extend(scan_errs)
    try:
        data = loads(content)
    except Exception as exc:
        return errs + [f"{path}: HCL parse error: {exc}"]

    if not isinstance(data, dict):
        return errs + [f"{path}: unexpected parse result"]

    terraform_blocks = data.get("terraform") or []
    providers = all_provider_entries(data)
    if not providers:
        errs.append(f"{path}: missing or empty required_providers")
        return errs

    child_map = {e.name: (e.version, e.source) for e in providers}
    child_rv = terraform_required_version(terraform_blocks)

    if root.required_version is not None and child_rv != root.required_version:
        errs.append(
            f"{path}: required_version must match root versions.tf ({root.required_version!r}), "
            f"got {child_rv!r}"
        )

    for name, (root_ver, root_src) in root.providers.items():
        if name not in child_map:
            if name in used:
                errs.append(
                    f"{path}: missing required_providers.{name} (must match root versions.tf)"
                )
            continue
        child_ver, child_src = child_map[name]
        if child_ver != root_ver:
            errs.append(
                f"{path}: required_providers.{name} version must match root ({root_ver!r}), "
                f"got {child_ver!r}"
            )
        if child_src != root_src:
            errs.append(
                f"{path}: required_providers.{name} source must match root ({root_src!r}), "
                f"got {child_src!r}"
            )

    return errs


def collect_versions_tf_paths(repo_root: Path) -> list[Path]:
    paths: list[Path] = []
    for sub in ("examples", "modules"):
        base = repo_root / sub
        if base.is_dir():
            paths.extend(sorted(base.rglob("versions.tf")))
    return paths


def validate_repo(repo_root: Path) -> list[str]:
    try:
        root = parse_root_versions_reference(repo_root)
    except (FileNotFoundError, ValueError) as exc:
        return [str(exc)]
    except Exception as exc:
        return [f"{repo_root / 'versions.tf'}: failed to parse root versions.tf: {exc}"]

    all_errs: list[str] = []
    for vf in collect_versions_tf_paths(repo_root):
        all_errs.extend(_errors_for_file(vf, vf.read_text(encoding="utf-8"), root))
    return all_errs


def main(
    repo_root: Path = typer.Option(
        Path.cwd(),
        "--repo-root",
        "-r",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        help="Terraform module repository root (contains versions.tf, examples/, modules/)",
    ),
) -> None:
    errors = validate_repo(repo_root)
    if errors:
        for line in errors:
            typer.echo(line, err=True)
        raise typer.Exit(1)
    typer.echo(f"validate-versions-tf: OK ({len(collect_versions_tf_paths(repo_root))} files)")


if __name__ == "__main__":
    typer.run(main)
