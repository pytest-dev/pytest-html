# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import pytest
from pathlib import Path

from . import extras  # noqa: F401
from .html_report import HTMLReport
from .nextgen import NextGenReport
from .nextgen import NextGenSelfContainedReport


def pytest_addhooks(pluginmanager):
    from . import hooks

    pluginmanager.add_hookspecs(hooks)


def pytest_addoption(parser):
    group = parser.getgroup("terminal reporting")
    group.addoption(
        "--html",
        action="store",
        dest="htmlpath",
        metavar="path",
        default=None,
        help="create html report file at given path.",
    )
    group.addoption(
        "--self-contained-html",
        action="store_true",
        help="create a self-contained html file containing all "
        "necessary styles, scripts, and images - this means "
        "that the report may not render or function where CSP "
        "restrictions are in place (see "
        "https://developer.mozilla.org/docs/Web/Security/CSP)",
    )
    group.addoption(
        "--css",
        action="append",
        metavar="path",
        default=[],
        help="append given css file content to report style file.",
    )
    group.addoption(
        "--next-gen",
        action="store_true",
        default=False,
        help="use next-gen report.",
    )
    parser.addini(
        "render_collapsed",
        type="bool",
        default=False,
        help="Open the report with all rows collapsed. Useful for very large reports",
    )
    parser.addini(
        "max_asset_filename_length",
        default=255,
        help="set the maximum filename length for assets "
        "attached to the html report.",
    )
    parser.addini(
        "environment_table_redact_list",
        type="linelist",
        help="A list of regexes corresponding to environment "
        "table variables whose values should be redacted from the report",
    )


def pytest_configure(config):
    html_path = config.getoption("htmlpath")
    if html_path:
        missing_css_files = []
        for css_path in config.getoption("css"):
            if not Path(css_path).exists():
                missing_css_files.append(css_path)

        if missing_css_files:
            os_error = (
                f"Missing CSS file{'s' if len(missing_css_files) > 1 else ''}:"
                f" {', '.join(missing_css_files)}"
            )
            raise OSError(os_error)

        if not hasattr(config, "workerinput"):
            # prevent opening html_path on worker nodes (xdist)

            if not config.getoption("next_gen"):
                html = HTMLReport(html_path, config)
            else:
                if config.getoption("self_contained_html"):
                    html = NextGenSelfContainedReport(html_path, config)
                else:
                    html = NextGenReport(html_path, config)

            config.pluginmanager.register(html)


def pytest_unconfigure(config):
    html = config.pluginmanager.getplugin("html")
    if html:
        config.pluginmanager.unregister(html)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call":
        fixture_extras = getattr(item.config, "extras", [])
        plugin_extras = getattr(report, "extra", [])
        report.extra = fixture_extras + plugin_extras


@pytest.fixture
def extra(pytestconfig):
    """Add details to the HTML reports.

    .. code-block:: python

        import pytest_html


        def test_foo(extra):
            extra.append(pytest_html.extras.url("https://www.example.com/"))
    """
    pytestconfig.extras = []
    yield pytestconfig.extras
    del pytestconfig.extras[:]
