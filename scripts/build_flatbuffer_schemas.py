"""Automatically generates submodule for parsing tree metadata flatbuffer."""

from pathlib import Path
import subprocess

root = Path(__file__).parent.parent


def main() -> None:
    """Automatically generates submodule for parsing tree metadata flatbuffer."""
    subprocess.run(
        ["flatc", "-p", "-o", "mtpy/utils/", "mtpy/utils/tree_metdata.fbs"],
        check=True,
    )
