import json
from functools import partial
from typing import Any
from typing import Dict


try:
    from ansi2html import Ansi2HTMLConverter, style

    converter = Ansi2HTMLConverter(inline=False, escaped=False)
    _handle_ansi = partial(converter.convert, full=False)
    _ansi_styles = style.get_styles()
except ImportError:
    from _pytest.logging import _remove_ansi_escape_sequences

    _handle_ansi = _remove_ansi_escape_sequences
    _ansi_styles = []


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
