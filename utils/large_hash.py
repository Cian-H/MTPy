from hashlib import sha1
from pathlib import Path


# A function for efficiently hashing large files
def large_hash(filename: str | Path, chunksize: int = 8192) -> int:
    with open(filename, "rb") as f:
        file_hash = sha1()
        while chunk := f.read(chunksize):
            file_hash.update(chunk)
    return int.from_bytes(file_hash.digest(), "big")