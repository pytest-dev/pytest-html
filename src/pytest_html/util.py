import importlib
import json
from functools import lru_cache
from typing import Any
from typing import Dict


@lru_cache()
def ansi_support():
    try:
        # from ansi2html import Ansi2HTMLConverter, style  # NOQA
        return importlib.import_module("ansi2html")
    except ImportError:
        # ansi2html is not installed
        pass


def cleanup_unserializable(d: Dict[str, Any]) -> Dict[str, Any]:
    """Return new dict with entries that are not json serializable by their str()."""
    result = {}
    for k, v in d.items():
        try:
            json.dumps({k: v})
        except TypeError:
            v = str(v)
        result[k] = v
    return result
