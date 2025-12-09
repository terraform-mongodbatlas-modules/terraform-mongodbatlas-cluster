from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# .github/tf_ws/ -> repo root
REPO_ROOT = Path(__file__).parent.parent.parent
DEFAULT_TESTS_DIR = REPO_ROOT / "tests"


@dataclass
class WsVar:
    name: str
    expose_in_workspace: bool = True


@dataclass
class SkipLines:
    substring_attributes: list[str] = field(default_factory=list)
    substring_values: list[str] = field(default_factory=list)


@dataclass
class DumpConfig:
    skip_lines: SkipLines = field(default_factory=SkipLines)


@dataclass
class PlanRegression:
    address: str
    dump: DumpConfig = field(default_factory=DumpConfig)


@dataclass
class Example:
    number: int
    var_groups: list[str] = field(default_factory=list)
    plan_regressions: list[PlanRegression] = field(default_factory=list)

    def example_path(self, examples_dir: Path) -> Path:
        for p in examples_dir.iterdir():
            if p.is_dir() and p.name.startswith(f"{self.number:02d}_"):
                return p
        raise ValueError(f"Example {self.number:02d}_* not found in {examples_dir}")


@dataclass
class WsConfig:
    examples: list[Example]
    var_groups: dict[str, list[WsVar]]

    def skip_attributes(self) -> list[str]:
        return [v.name for vs in self.var_groups.values() for v in vs]

    def exposed_vars(self) -> list[WsVar]:
        seen: set[str] = set()
        result: list[WsVar] = []
        for vs in self.var_groups.values():
            for v in vs:
                if v.expose_in_workspace and v.name not in seen:
                    seen.add(v.name)
                    result.append(v)
        return result


def parse_ws_config(ws_yaml_path: Path) -> WsConfig:
    data = yaml.safe_load(ws_yaml_path.read_text())
    var_groups: dict[str, list[WsVar]] = {}
    for group_name, vars_list in data.get("var_groups", {}).items():
        var_groups[group_name] = [
            WsVar(
                name=v["name"], expose_in_workspace=v.get("expose_in_workspace", True)
            )
            for v in vars_list
        ]
    examples: list[Example] = []
    for ex in data.get("examples", []):
        regressions = [
            PlanRegression(
                address=r["address"],
                dump=_parse_dump_config(r.get("dump", {})),
            )
            for r in ex.get("plan_regressions", [])
        ]
        examples.append(
            Example(
                number=ex["number"],
                var_groups=ex.get("var_groups", []),
                plan_regressions=regressions,
            )
        )
    return WsConfig(examples=examples, var_groups=var_groups)


def _parse_dump_config(data: dict[str, Any]) -> DumpConfig:
    skip = data.get("skip_lines", {})
    return DumpConfig(
        skip_lines=SkipLines(
            substring_attributes=skip.get("substring_attributes", []),
            substring_values=skip.get("substring_values", []),
        )
    )


def sanitize_address(address: str) -> str:
    return address.replace(".", "_")


def resolve_workspaces(ws: str, tests_dir: Path = DEFAULT_TESTS_DIR) -> list[Path]:
    """Resolve workspace directories based on ws name.

    Args:
        ws: Workspace name or 'all' for all ws_* directories
        tests_dir: Path to tests directory

    Returns:
        List of workspace directory paths

    Raises:
        ValueError: If tests_dir doesn't exist, ws not found, or no ws_* dirs found
    """
    if not tests_dir.exists():
        raise ValueError(f"{tests_dir} does not exist")
    if ws == "all":
        ws_dirs = sorted(
            d for d in tests_dir.iterdir() if d.is_dir() and d.name.startswith("ws_")
        )
        if not ws_dirs:
            raise ValueError(f"No ws_* directories found in {tests_dir}")
        return ws_dirs
    ws_path = tests_dir / ws
    if not ws_path.exists():
        raise ValueError(f"{ws_path} does not exist")
    return [ws_path]
