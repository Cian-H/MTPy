"""A module for adding and reading metadata tags to and from files."""

import json
from typing import cast

from fsspec.spec import AbstractFileSystem

from mtpy.utils.type_guards import guarded_bytes
from mtpy.utils.types import JSONData


def add_metadata(fs: AbstractFileSystem, file: str, meta: JSONData) -> None:
    """A function for adding a metadata tag to a file.

    Args:
        fs (AbstractFileSystem): an fsspec filesystem
        file (str): the file to add the metadata tag to
        meta (JSONDict): the metadata tag to add
    """
    serialized_meta = json.dumps(meta).encode("utf-8")
    with fs.open(file, "ab+") as f:
        f.write(serialized_meta)
        f.write(
            # this being bytes instead of str is fine because `mode` is "ab+"
            cast(str, len(serialized_meta).to_bytes(8, "big"))
        )


def read_metadata(fs: AbstractFileSystem, file: str) -> JSONData:
    """A function for reading a metadata tag from a file.

    Args:
        fs (AbstractFileSystem): an fsspec filesystem
        file (str): the file to read the metadata tag from

    Returns:
        JSONDict: the metadata tag read from the file
    """
    with fs.open(file, "rb") as f:
        f.seek(-8, 2)
        json_size = int.from_bytes(
            guarded_bytes(f.read()),  # this will be bytes because `mode` is "rb"
            "big",
        )
        f.seek(-8 - json_size, 2)
        data = f.read(json_size)
    return json.loads(data)
