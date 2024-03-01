from __future__ import annotations

from typing import Any, AnyStr, Dict


def apply_defaults(dict: Dict[AnyStr, Any], defaults_dict: Dict[AnyStr, Any]) -> Dict[AnyStr, Any]:
    """A function for applying defaults to a dicts, intended for applying default kwargs.
    (DEPRECATED: will switch to using dict.update(defaults_dict) instead)

    Args:
        dict (Dict[AnyStr, Any]): the dict to apply to
        defaults_dict (Dict[AnyStr, Any]): the dict to apply

    Returns:
        dict: the updated Dict[AnyStr, Any]
    """
    keys = set(dict.keys()).union(set(defaults_dict.keys()))
    return {k: dict.get(k, defaults_dict.get(k)) for k in keys}
