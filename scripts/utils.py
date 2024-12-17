"""Shared utility objects for project scripts."""

from pathlib import Path
import tomlkit


ROOT = Path(__file__).parent.parent
SRC = ROOT / "mtpy"
PYPROJECT_TOML = ROOT / "pyproject.toml"


def read_pyproject() -> tomlkit.TOMLDocument:
    """Read pyproject file via tomlkit."""
    with PYPROJECT_TOML.open("rt") as pyproj_file:
        return tomlkit.load(pyproj_file)
