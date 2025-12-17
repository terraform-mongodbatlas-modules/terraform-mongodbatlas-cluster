"""Generate dev.tfvars for workspace tests."""

from pathlib import Path

import typer

app = typer.Typer()

WORKSPACE_DIR = Path(__file__).parent.parent.parent / "tests" / "workspace_cluster_examples"
DEV_TFVARS = WORKSPACE_DIR / "dev.tfvars"


@app.command()
def project(project_id: str) -> None:
    content = f"""project_ids = {{
    project1 = "{project_id}"
    project2 = "{project_id}"
    project3 = "{project_id}"
    project4 = "{project_id}"
    project5 = "{project_id}"
}}
"""
    DEV_TFVARS.write_text(content)
    typer.echo(f"Generated {DEV_TFVARS}")


@app.command()
def org(org_id: str) -> None:
    content = f'org_id = "{org_id}"\n'
    DEV_TFVARS.write_text(content)
    typer.echo(f"Generated {DEV_TFVARS}")


if __name__ == "__main__":
    app()
