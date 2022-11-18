from __future__ import annotations

from pathlib import Path
import json


def add_metadata(image: str | Path, meta: any) -> None:
    meta = json.dumps(meta).encode("utf-8")
    with open(image, "ab+") as f:
        f.write(meta)
        f.write(len(meta).to_bytes(8, "big"))

def read_metadata(image: str | Path) -> any:
    with open(image, "rb") as f:
        f.seek(-8, 2)
        json_size = int.from_bytes(f.read(), "big")
        f.seek(-8 - json_size, 2)
        data = f.read(json_size)
    return json.loads(data)