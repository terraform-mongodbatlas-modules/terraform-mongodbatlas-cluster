from __future__ import annotations

from pathlib import Path

from docs import config_loader
from docs import root_readme as mod


def test_extract_getting_started_basic() -> None:
    template = """# Example
<!-- BEGIN_GETTING_STARTED -->
## Pre Requirements

Some prereqs here.

## Commands

```sh
terraform init
```
<!-- END_GETTING_STARTED -->
## Other Section
"""
    result = mod.extract_getting_started(template)
    assert "### Pre Requirements" in result
    assert "### Commands" in result
    assert result.startswith("### ")  # headings downgraded from ##
    assert result.endswith("\n")  # ensure trailing newline is present
    assert "Other Section" not in result


def test_extract_getting_started_no_markers() -> None:
    template = "# Example\n## Section\nContent"
    assert mod.extract_getting_started(template) == ""


def test_generate_tables_with_extra_columns(tmp_path: Path) -> None:
    examples_dir = tmp_path / "examples"
    (examples_dir / "01_basic").mkdir(parents=True)
    table = config_loader.TableConfig(
        name="Test",
        columns=["feature", "name", "description"],
        link_column="name",
        example_rows=[
            config_loader.ExampleRow(
                name="Basic", folder=1, feature="Setup", description="A basic example"
            ),
        ],
    )
    result = mod.generate_tables([table], examples_dir)
    assert "[Basic](./examples/01_basic)" in result
    assert "Setup" in result
    assert "A basic example" in result


def test_generate_tables_auto_columns(tmp_path: Path) -> None:
    examples_dir = tmp_path / "examples"
    example_dir = examples_dir / "01_basic"
    example_dir.mkdir(parents=True)
    (example_dir / "main.tf").write_text('cluster_type = "REPLICASET"')
    table = config_loader.TableConfig(
        name="Test",
        columns=["cluster_type", "name"],
        link_column="name",
        auto_columns={
            "cluster_type": config_loader.AutoColumnConfig(
                file="main.tf",
                pattern=r'cluster_type\s*=\s*"(?P<value>[^"]+)"',
            ),
        },
        example_rows=[config_loader.ExampleRow(name="Basic", folder=1)],
    )
    result = mod.generate_tables([table], examples_dir)
    assert "REPLICASET" in result


def test_generate_tables_explicit_extra_overrides_auto(tmp_path: Path) -> None:
    examples_dir = tmp_path / "examples"
    example_dir = examples_dir / "01_basic"
    example_dir.mkdir(parents=True)
    (example_dir / "main.tf").write_text('cluster_type = "REPLICASET"')
    table = config_loader.TableConfig(
        name="Test",
        columns=["cluster_type", "name"],
        link_column="name",
        auto_columns={
            "cluster_type": config_loader.AutoColumnConfig(
                file="main.tf",
                pattern=r'cluster_type\s*=\s*"(?P<value>[^"]+)"',
            ),
        },
        example_rows=[
            config_loader.ExampleRow(name="Basic", folder=1, cluster_type="Multiple"),
        ],
    )
    result = mod.generate_tables([table], examples_dir)
    assert "Multiple" in result
    assert "REPLICASET" not in result


def test_resolve_auto_column_file_not_found(tmp_path: Path) -> None:
    auto_config = config_loader.AutoColumnConfig(
        file="missing.tf",
        pattern=r'key\s*=\s*"(?P<value>[^"]+)"',
    )
    assert mod._resolve_auto_column(auto_config, tmp_path) == ""


def test_resolve_auto_column_pattern_no_match(tmp_path: Path) -> None:
    (tmp_path / "main.tf").write_text("no_match_here = true")
    auto_config = config_loader.AutoColumnConfig(
        file="main.tf",
        pattern=r'cluster_type\s*=\s*"(?P<value>[^"]+)"',
    )
    assert mod._resolve_auto_column(auto_config, tmp_path) == ""


def test_generate_toc_ampersand_produces_double_hyphen() -> None:
    content = "## AWS Cloud Provider Access & IAM Policy\n## Simple Heading\n"
    result = mod.generate_toc_from_headings(content)
    assert "(#aws-cloud-provider-access--iam-policy)" in result
    assert "(#simple-heading)" in result


def test_downgrade_headers() -> None:
    content = """\
# H1 stays the same
## H2 becomes H3
### H3 becomes H4
#### H4 becomes H5
Regular text stays the same
##No space also works"""
    result = mod.downgrade_headers(content)
    assert "# H1 stays the same" in result  # H1 unchanged
    assert "### H2 becomes H3" in result
    assert "#### H3 becomes H4" in result
    assert "##### H4 becomes H5" in result
    assert "Regular text stays the same" in result
    assert "###No space also works" in result
