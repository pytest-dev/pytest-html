from pkg_resources import get_distribution, DistributionNotFound


try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    pass

__pypi_url__ = 'https://pypi.python.org/pypi/pytest-html'
