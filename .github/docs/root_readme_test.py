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
    assert result.endswith("\n")  # ensure trailing newline is present
    assert "Other Section" not in result


def test_extract_getting_started_no_markers() -> None:
    template = "# Example\n## Section\nContent"
    assert mod.extract_getting_started(template) == ""


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
