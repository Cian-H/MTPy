from __future__ import annotations

from hashlib import sha1 as default_hash
from _hashlib import HASH as Hash


def hash_update_from_file(fs, filepath: str, hash: Hash) -> Hash:
    """A function for updating a hash object with the name and checksum of a file

    Args:
        fs (filesystem): an fsspec filesystem
        filepath (str): a path to hte file or directory to hash
        hash (Hash): the hashlib hash object to update

    Returns:
        Hash: a hashlib hash object
    """
    hash.update(fs.info(filepath)["name"].split("/")[1].encode())
    chk = fs.checksum(filepath)
    hash.update(chk.to_bytes(chk.bit_length(), "big"))
    return hash


# A function for efficiently hashing large files and directories
def large_hash(fs, filepath: str, hash: None | Hash = None) -> int:
    """a function for efficiently hashing large files and directories

    Args:
        fs (filesystem): an fsspec filesystem
        filepath (str): a path to hte file or directory to hash
        hash (None | Hash, optional): the hashlib hash object to apply.
            Defaults to None.

    Returns:
        int: the hash result as an integer
    """
    if hash is None:
        hash = default_hash()
    if fs.isfile(filepath):
        hash = hash_update_from_file(fs, filepath, hash)
    elif fs.isdir(filepath):
        for path in sorted(fs.find(filepath)):
            hash = hash_update_from_file(fs, path, hash)
    return int.from_bytes(hash.digest(), "big")
