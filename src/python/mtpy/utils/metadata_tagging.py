from __future__ import annotations

import json


def add_metadata(fs, file: str, meta: any) -> None:
    """a function for adding a metadata tag to a file

    Args:
        fs (filesystem): an fspec filesystem
        file (str): the file to add the metadata tag to
        meta (any): the metadata tag to add
    """
    meta = json.dumps(meta).encode("utf-8")
    with fs.open(file, "ab+") as f:
        f.write(meta)
        f.write(len(meta).to_bytes(8, "big"))


def read_metadata(fs, file: str) -> any:
    """a function for reading a metadata tag from a file

    Args:
        fs (filesystem): an fspec filesystem
        file (str): the file to read the metadata tag from

    Returns:
        any: the metadata tag read from the file
    """
    with fs.open(file, "rb") as f:
        f.seek(-8, 2)
        json_size = int.from_bytes(f.read(), "big")
        f.seek(-8 - json_size, 2)
        data = f.read(json_size)
    return json.loads(data)
