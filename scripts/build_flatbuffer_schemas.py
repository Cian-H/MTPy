"""Automatically generates submodule for parsing tree metadata flatbuffer."""

from importlib.machinery import SourceFileLoader
from pathlib import Path
import subprocess

utils = SourceFileLoader("utils", str(Path(__file__).parent / "utils.py")).load_module()


def main() -> None:
    """Automatically generates submodule for parsing tree metadata flatbuffer."""
    subprocess.run(
        ["flatc", "-p", "-o", f"{utils.SRC}/utils/", f"{utils.SRC}/utils/tree_metdata.fbs"],
        check=True,
    )
