def apply_defaults(dict: dict, defaults_dict: dict) -> dict:
    keys = set(dict.keys()).union(set(defaults_dict.keys()))
    return {k: dict.get(k, defaults_dict[k]) for k in keys}