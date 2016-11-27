from pkg_resources import get_distribution, DistributionNotFound
try:
    dist = get_distribution(__name__)
except DistributionNotFound:
    # package is not installed
    pass
else:
    __version__ = dist.version
    metadata = dist._get_metadata(dist.PKG_INFO)
    home_page = [m for m in metadata if m.startswith('Home-page:')]
    __pypi_url__ = home_page[0].split(':', 1)[1].strip()
