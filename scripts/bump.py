"""Bump package semver and sync pyproject metadata to __init__."""

from importlib.machinery import SourceFileLoader
from pathlib import Path

semver_pyproj = SourceFileLoader(
    "semver_pyproj", str(Path(__file__).parent / "semver_pyproj.py")
).load_module()
sync_init_vars = SourceFileLoader(
    "sync_init_vars", str(Path(__file__).parent / "sync_init_vars.py")
).load_module()


def main() -> None:
    """Bump package semver and sync pyproject metadata to __init__."""
    semver_pyproj.main()
    sync_init_vars.main()
