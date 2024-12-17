"""Syncs metadata variables from pyproject.toml to __init__.py."""

from importlib.machinery import SourceFileLoader
from pathlib import Path

utils = SourceFileLoader("utils", str(Path(__file__).parent / "utils.py")).load_module()

METADATA_KEYS = ("description", "version", "authors", "license", "urls")


def main() -> None:
    """Syncs metadata variables from pyproject.toml to __init__.py."""
    pyproj = utils.read_pyproject()
    try:
        poetry_entry = pyproj["tool"]["poetry"]
    except KeyError as e:
        raise e
    if not isinstance(poetry_entry, dict):
        msg = f"Expected poetry entry to be of type dict, got type {type(poetry_entry)}"
        raise TypeError(msg)
    init_src = utils.SRC / "__init__.py"
    with init_src.open("rt") as f:
        in_lines = f.readlines()
    out_lines = []
    for line in in_lines:
        for k in METADATA_KEYS:
            if line.startswith(f"__{k}__ = "):
                out_lines.append(f"__{k}__ = {poetry_entry[k].__repr__().replace("'", '"')}\n")
                break
        else:
            out_lines.append(line)
    init_src.unlink(missing_ok=True)
    with (init_src).open("wt") as f:
        f.writelines(out_lines)
