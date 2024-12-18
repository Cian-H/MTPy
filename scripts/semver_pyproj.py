"""Automatically and interactively bump semver for this module."""

from importlib.machinery import SourceFileLoader
from pathlib import Path

import inquirer
from loguru import logger
import semver
import tomlkit

utils = SourceFileLoader("utils", str(Path(__file__).parent / "utils.py")).load_module()


change_dispatch = {
    "Patch": semver.Version.bump_patch,
    "Minor": semver.Version.bump_minor,
    "Major": semver.Version.bump_major,
}


def main() -> None:
    """Interactively update semver version in pyproject.toml."""
    pyproj = utils.read_pyproject()
    version = get_version(pyproj)
    version = bump(version)
    set_version(pyproj, version)


def bump(version: semver.Version) -> semver.Version:
    """Interactively bump semver version."""
    response = inquirer.prompt(
        [
            inquirer.Checkbox(
                "change_types",
                message="What kind of change has been made?",
                choices=list(change_dispatch.keys()),
            )
        ]
    )
    out = version
    for change in response["change_types"]:
        out = change_dispatch[change](out)  # type: ignore
    return out


def get_version(pyproj: tomlkit.TOMLDocument) -> semver.Version:
    """Get semantic version from pyproject.toml."""
    entry = pyproj
    try:
        for e in ("tool", "poetry", "version"):
            if isinstance(entry, dict):
                entry = entry[e]
            elif not isinstance(entry, str):
                raise KeyError(err_msg(e))
            elif e != "version":
                msg = "[e] is type `str`"
                raise KeyError(msg)
            else:
                break
        if not isinstance(entry, str):
            msg = f"[tool.poetry.version] was expected to be type `str`, got type {type(entry)}"
            raise TypeError(msg)
    except (KeyError, TypeError) as e:
        logger.error(e)
        entry = "0.0.0"
    return semver.Version.parse(entry)


def set_version(pyproj: tomlkit.TOMLDocument, version: semver.Version) -> None:
    """Set semantic version in pyproject.toml and __init__.py."""
    entry = pyproj
    for e in ("tool", "poetry"):
        entry = entry.get(e, {})
        if not isinstance(entry, dict):
            raise KeyError(err_msg(e))
    entry["version"] = str(version)
    utils.PYPROJECT_TOML.unlink(missing_ok=True)
    with utils.PYPROJECT_TOML.open("wt") as pyproj_file:
        tomlkit.dump(pyproj, pyproj_file)


def err_msg(entry: str) -> str:
    """Creates key error in pyproject.toml message."""
    return f"[{entry}] not found in pyproject.toml"
