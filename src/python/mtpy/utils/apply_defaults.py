from __future__ import annotations


#
def apply_defaults(dict: dict, defaults_dict: dict) -> dict:
    """A function for applying defaults to a dicts, intended for applying default kwargs.
    (DEPRECATED: will switch to using dict.update(defaults_dict) instead)

    Args:
        dict (dict): the dict to apply to
        defaults_dict (dict): the dict to apply

    Returns:
        dict: the updated dict
    """
    keys = set(dict.keys()).union(set(defaults_dict.keys()))
    return {k: dict.get(k, defaults_dict.get(k)) for k in keys}
