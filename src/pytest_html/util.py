import importlib
from functools import lru_cache


@lru_cache()
def ansi_support():
    try:
        # from ansi2html import Ansi2HTMLConverter, style  # NOQA
        return importlib.import_module("ansi2html")
    except ImportError:
        # ansi2html is not installed
        pass
