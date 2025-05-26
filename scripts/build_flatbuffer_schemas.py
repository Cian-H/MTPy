"""Automatically generates submodule for parsing tree metadata flatbuffer."""

import subprocess

from scripts import utils


def main() -> None:
    """Automatically generates submodule for parsing tree metadata flatbuffer."""
    subprocess.run(
        ["flatc", "-p", "-o", f"{utils.SRC}/utils/", f"{utils.SRC}/utils/tree_metdata.fbs"],
        check=True,
    )
