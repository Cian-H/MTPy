"""Generates a UML diagram of the module."""

import subprocess

from scripts import utils

UML_DIR = utils.get_mkdocs_site_dir() / "docs/uml/"

UML_DIR.mkdir(parents=True, exist_ok=True)

subprocess.run(
    ["pyreverse", utils.ROOT / "mtpy", "-o", "mmd", "-d", UML_DIR],
    check=True,
)

with (
    (UML_DIR / "classes.mmd").open("rt") as classes,
    (UML_DIR / "packages.mmd").open("rt") as packages,
    (UML_DIR.parent / "uml.md").open("wt+") as uml,
):
    uml.write(
        f'=== "Packages"\n    ```mermaid\n    {"\n    ".join(packages.readlines())}    ```\n=== "Classes"\n    ```mermaid\n    {"\n    ".join(classes.readlines())}\n    ```'  # noqa
    )
