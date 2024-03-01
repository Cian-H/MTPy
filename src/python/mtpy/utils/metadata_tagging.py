from __future__ import annotations

import json
from typing import Any, cast

from fsspec.spec import AbstractFileSystem


def add_metadata(fs: AbstractFileSystem, file: str, meta: Any) -> None:
    """a function for adding a metadata tag to a file

    Args:
        fs (AbstractFileSystem): an fsspec filesystem
        file (str): the file to add the metadata tag to
        meta (Any): the metadata tag to add
    """
    meta = json.dumps(meta).encode("utf-8")
    with fs.open(file, "ab+") as f:
        f.write(meta)
        f.write(
            # this being bytes instead of str is fine because `mode` is "ab+"
            cast(str, len(meta).to_bytes(8, "big"))
        )


def read_metadata(fs: AbstractFileSystem, file: str) -> Any:
    """a function for reading a metadata tag from a file

    Args:
        fs (AbstractFileSystem): an fsspec filesystem
        file (str): the file to read the metadata tag from

    Returns:
        any: the metadata tag read from the file
    """
    with fs.open(file, "rb") as f:
        f.seek(-8, 2)
        json_size = int.from_bytes(
            cast(bytes, f.read()),  # this will be bytes because `mode` is "rb"
            "big",
        )
        f.seek(-8 - json_size, 2)
        data = f.read(json_size)
    return json.loads(data)
