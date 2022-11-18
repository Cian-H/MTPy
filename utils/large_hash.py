from __future__ import annotations

from hashlib import sha1 as default_hash
from _hashlib import HASH as Hash
from pathlib import Path


def hash_update_from_file(filepath: Path, hash: Hash, chunksize: int) -> Hash:
    with open(filepath, "rb") as f:
        while chunk := f.read(chunksize):# for chunk in iter(lambda: f.read(chunksize), b""):
            hash.update(chunk)
    return hash


def hash_update_from_dir(directory: Path, hash: Hash, chunksize: int) -> Hash:
    for path in sorted(directory.iterdir()):
        hash.update(path.name.encode())
        if path.is_file():
            hash = hash_update_from_file(path, hash, chunksize)
        elif path.is_dir():
            hash = hash_update_from_dir(path, hash, chunksize)
    return hash


# A function for efficiently hashing large files and directories
def large_hash(filepath: str | Path, hash: None | Hash = None, chunksize: int = 8192) -> int:
    if hash is None:
        hash = default_hash()
    if not isinstance(filepath, Path):
        filepath = Path(filepath)
    if filepath.is_file():
        hash_result = hash_update_from_file(filepath, hash, chunksize)
    elif filepath.is_dir():
        hash_result = hash_update_from_dir(filepath, hash, chunksize)
    return int.from_bytes(hash.digest(), "big")