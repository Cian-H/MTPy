from __future__ import annotations

# A function for applying defaults to a dicts, intended for applying default kwargs
def apply_defaults(dict: dict, defaults_dict: dict) -> dict:
    keys = set(dict.keys()).union(set(defaults_dict.keys()))
    return {k: dict.get(k, defaults_dict.get(k)) for k in keys}