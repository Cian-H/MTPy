# -*- coding: utf-8 -*-

"""A module containing functions for efficiently hashing large files and directories."""

from __future__ import annotations

from hashlib import sha1 as default_hash
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from _hashlib import HASH
    from fsspec import AbstractFileSystem


def hash_update_from_file(fs: AbstractFileSystem, filepath: str, _hash: HASH) -> HASH:
    """A function for updating a hash object with the name and checksum of a file.

    Args:
        fs (AbstractFileSystem): an fsspec filesystem
        filepath (str): a path to hte file or directory to hash
        hash (Hash): the hashlib hash object to update

    Returns:
        Hash: a hashlib hash object
    """
    _hash.update(fs.info(filepath)["name"].split("/")[1].encode())
    chk = fs.checksum(filepath)
    _hash.update(chk.to_bytes(chk.bit_length(), "big"))
    return _hash


# A function for efficiently hashing large files and directories
def large_hash(fs: AbstractFileSystem, filepath: str, _hash: Optional[HASH] = None) -> int:
    """A function for efficiently hashing large files and directories.

    Args:
        fs (AbstractFileSystem): an fsspec filesystem
        filepath (str): a path to the file or directory to hash
        hash (Optional[Hash], optional): the hashlib hash object to apply.
            Defaults to None.

    Returns:
        int: the hash result as an integer
    """
    hash_obj = default_hash() if _hash is None else _hash
    if fs.isfile(filepath):
        hash_obj = hash_update_from_file(fs, filepath, hash_obj)
    elif fs.isdir(filepath):
        for path in sorted(fs.find(filepath)):
            hash_obj = hash_update_from_file(fs, path, hash_obj)
    return int.from_bytes(hash_obj.digest(), "big")
