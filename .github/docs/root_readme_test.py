from __future__ import annotations

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
    assert "Other Section" not in result


def test_extract_getting_started_no_markers() -> None:
    template = "# Example\n## Section\nContent"
    assert mod.extract_getting_started(template) == ""
