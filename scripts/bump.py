"""Bump package semver and sync pyproject metadata to __init__."""

from scripts import semver_pyproj, sync_init_vars


def main() -> None:
    """Bump package semver and sync pyproject metadata to __init__."""
    semver_pyproj.main()
    sync_init_vars.main()
