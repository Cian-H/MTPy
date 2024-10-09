"""Generates a UML diagram of the module."""

from pathlib import Path
import subprocess

root = Path(__file__).parent.parent
uml_dir = root / "docs/uml/"

uml_dir.mkdir(parents=True, exist_ok=True)

subprocess.run(
    ["pyreverse", root / "mtpy", "-o", "mmd", "-d", uml_dir],
    check=True,
)

with (
    Path("docs/uml/classes.mmd").open("rt") as classes,
    Path("docs/uml/packages.mmd").open("rt") as packages,
    Path("docs/uml.md").open("wt+") as uml,
):
    uml.write(
        f'=== "Packages"\n    ```mermaid\n    {"\n    ".join(packages.readlines())}    ```\n=== "Classes"\n    ```mermaid\n    {"\n    ".join(classes.readlines())}\n    ```'  # noqa
    )
