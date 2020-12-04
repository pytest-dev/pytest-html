try:
    from . import __version

    __version__ = __version.version
except ImportError:
    # package is not built with setuptools_scm
    __version__ = "unknown"

__pypi_url__ = "https://pypi.python.org/pypi/pytest-html"
