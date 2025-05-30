"""Shared utility objects for project scripts."""

from pathlib import Path
from typing import Any, Dict

import tomlkit

ROOT = Path(__file__).parent.parent
SRC = ROOT / "mtpy"
PYPROJECT_TOML = ROOT / "pyproject.toml"


def read_pyproject() -> tomlkit.TOMLDocument:
    """Read pyproject file via tomlkit."""
    with PYPROJECT_TOML.open("rt") as pyproj_file:
        return tomlkit.load(pyproj_file)


def get_mkdocs_config() -> Dict[str, Any]:
    """Get the config for mkdocs at built time."""
    import mkdocs_gen_files

    return mkdocs_gen_files.config


def get_mkdocs_site_dir() -> Path:
    """Get the site-dir argument for mkdocs at build time."""
    config = get_mkdocs_config()
    return Path(config["site_dir"])


def get_mkdocs_docs_dir() -> Path:
    """Get the site-dir argument for mkdocs at build time."""
    config = get_mkdocs_config()
    return Path(config["docs_dir"])


def get_mkdocs_generated_assets_dir() -> Path:
    """Get the directory for generated static assets at mkdocs build time."""
    return get_mkdocs_docs_dir() / "assets/generated"
