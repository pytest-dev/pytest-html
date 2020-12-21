import importlib
from functools import lru_cache
from types import ModuleType
from typing import Optional


@lru_cache()
def ansi_support() -> Optional[ModuleType]:
    try:
        # from ansi2html import Ansi2HTMLConverter, style  # NOQA
        return importlib.import_module("ansi2html")
    except ImportError:
        # ansi2html is not installed
        return None
