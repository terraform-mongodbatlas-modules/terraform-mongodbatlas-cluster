from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).parent.parent.parent
DEFAULT_TESTS_DIR = REPO_ROOT / "tests"


@dataclass
class WsVar:
    name: str
    expose_in_workspace: bool = True
    module_value: str = ""
    var_type: str = ""


DEFAULT_REDACT_ATTRIBUTES: list[str] = [
    "secret",
    "password",
    "token",
    "credentials",
    "private_key",
    "client_secret",
    "tenant_id",
]


@dataclass
class SkipLines:
    substring_attributes: list[str] = field(default_factory=list)
    substring_values: list[str] = field(default_factory=list)
    redact_attributes: list[str] = field(default_factory=list)
    use_default_redact: bool = True


@dataclass
class DumpConfig:
    skip_lines: SkipLines = field(default_factory=SkipLines)


@dataclass
class PlanRegression:
    """Configuration for a plan regression test.

    Attributes:
        address: The exact resource address after the example prefix.
            Must be the full path as it appears in the terraform plan,
            minus the `module.ex_{example_id}.` prefix.

            For example, if the full plan address is:
                module.ex_encryption.module.atlas_azure.module.encryption[0].azurerm_role_assignment.key_vault_crypto

            The address should be:
                module.atlas_azure.module.encryption[0].azurerm_role_assignment.key_vault_crypto

            This ensures clear, unambiguous matching and makes it easy to find
            resources in the plan output.

        dump: Configuration for how to dump the resource values to YAML.
    """

    address: str
    dump: DumpConfig = field(default_factory=DumpConfig)


@dataclass
class Example:
    number: int | None = None
    name: str | None = None
    var_groups: list[str] = field(default_factory=list)
    plan_regressions: list[PlanRegression] = field(default_factory=list)

    @property
    def identifier(self) -> str:
        if self.name:
            return self.name
        if self.number is not None:
            return f"{self.number:02d}"
        raise ValueError("Example must have either name or number")

    def example_path(self, examples_dir: Path) -> Path:
        if self.name:
            path = examples_dir / self.name
            if not path.exists():
                raise ValueError(f"Example '{self.name}' not found in {examples_dir}")
            return path
        for p in examples_dir.iterdir():
            if p.is_dir() and p.name.startswith(f"{self.number:02d}_"):
                return p
        raise ValueError(f"Example {self.number:02d}_* not found in {examples_dir}")

    def title_from_dir(self, examples_dir: Path) -> str:
        dir_name = self.example_path(examples_dir).name
        if self.name:
            return dir_name.replace("_", " ").title()
        return dir_name.split("_", 1)[1].replace("_", " ").title()


@dataclass
class WsConfig:
    examples: list[Example]
    var_groups: dict[str, list[WsVar]]

    def redact_var_attributes(self) -> list[str]:
        """Variable names that should be redacted (not skipped) in snapshots."""
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

    def vars_for_example(self, example: Example) -> list[WsVar]:
        result: list[WsVar] = []
        seen: dict[str, str] = {}
        for group_name in example.var_groups:
            for var in self.var_groups.get(group_name, []):
                if var.name in seen:
                    raise ValueError(
                        f"Duplicate variable '{var.name}' in example {example.identifier}: "
                        f"defined in both '{seen[var.name]}' and '{group_name}'"
                    )
                seen[var.name] = group_name
                result.append(var)
        return result


def parse_ws_config(ws_yaml_path: Path) -> WsConfig:
    data = yaml.safe_load(ws_yaml_path.read_text())
    var_groups: dict[str, list[WsVar]] = {}
    for group_name, vars_list in data.get("var_groups", {}).items():
        var_groups[group_name] = [
            WsVar(
                name=v["name"],
                expose_in_workspace=v.get("expose_in_workspace", True),
                module_value=v.get("module_value", ""),
                var_type=v.get("var_type", ""),
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
                number=ex.get("number"),
                name=ex.get("name"),
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
            redact_attributes=skip.get("redact_attributes", []),
            use_default_redact=skip.get("use_default_redact", True),
        )
    )


def sanitize_address(address: str) -> str:
    return address.replace(".", "_")


WORKSPACE_CONFIG_FILE = "workspace_test_config.yaml"


def resolve_workspaces(workspace: str, tests_dir: Path = DEFAULT_TESTS_DIR) -> list[Path]:
    if not tests_dir.exists():
        raise ValueError(f"{tests_dir} does not exist")
    if workspace == "all":
        ws_dirs = sorted(
            d for d in tests_dir.iterdir() if d.is_dir() and d.name.startswith("workspace_")
        )
        if not ws_dirs:
            raise ValueError(f"No workspace_* directories found in {tests_dir}")
        return ws_dirs
    workspace_path = tests_dir / workspace
    if not workspace_path.exists():
        raise ValueError(f"{workspace_path} does not exist")
    workspace_config = workspace_path / WORKSPACE_CONFIG_FILE
    if not workspace_config.exists():
        raise ValueError(f"{workspace_config} does not exist")
    return [workspace_path]
