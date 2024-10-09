"""Generates a UML diagram of the module."""

from pathlib import Path
import subprocess

root = Path(__file__).parent.parent
uml_dir = root / "docs/uml/"

uml_dir.mkdir(parents=True, exist_ok=True)

subprocess.run(
    ["pyreverse", root / "mtpy", "-o", "html", "-d", uml_dir],
    check=True,
)
