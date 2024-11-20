# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import os
import warnings
from pathlib import Path

import pytest

from pytest_html import extras  # noqa: F401
from pytest_html.fixtures import extras_stash_key
from pytest_html.report import Report
from pytest_html.report_data import ReportData
from pytest_html.selfcontained_report import SelfContainedReport
from pytest_html.util import _process_css
from pytest_html.util import _read_template


def pytest_addhooks(pluginmanager):
    from pytest_html import hooks

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
    parser.addini(
        "render_collapsed",
        type="string",
        default="passed",
        help="row(s) to render collapsed on open.",
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
        help="a list of regexes corresponding to environment "
        "table variables whose values should be redacted from the report",
    )
    parser.addini(
        "initial_sort",
        type="string",
        default="result",
        help="column to initially sort on.",
    )
    parser.addini(
        "generate_report_on_test",
        type="bool",
        default=False,
        help="the HTML report will be generated after each test "
        "instead of at the end of the run.",
    )


def pytest_configure(config):
    html_path = config.getoption("htmlpath")
    if html_path:
        extra_css = [
            Path(os.path.expandvars(css)).expanduser()
            for css in config.getoption("css")
        ]
        missing_css_files = []
        for css_path in extra_css:
            if not css_path.exists():
                missing_css_files.append(str(css_path))

        if missing_css_files:
            os_error = (
                f"Missing CSS file{'s' if len(missing_css_files) > 1 else ''}:"
                f" {', '.join(missing_css_files)}"
            )
            raise OSError(os_error)

        if not hasattr(config, "workerinput"):
            # prevent opening html_path on worker nodes (xdist)
            resources_path = Path(__file__).parent.joinpath("resources")
            default_css = Path(resources_path, "style.css")
            template = _read_template([resources_path])
            processed_css = _process_css(default_css, extra_css)
            report_data = ReportData(config)
            if config.getoption("self_contained_html"):
                html = SelfContainedReport(
                    html_path, config, report_data, template, processed_css
                )
            else:
                html = Report(html_path, config, report_data, template, processed_css)

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
        deprecated_extra = getattr(report, "extra", [])
        if deprecated_extra:
            warnings.warn(
                "The 'report.extra' attribute is deprecated and will be removed in a future release"
                ", use 'report.extras' instead.",
                DeprecationWarning,
            )
        fixture_extras = item.config.stash.get(extras_stash_key, [])
        plugin_extras = getattr(report, "extras", [])
        report.extras = fixture_extras + plugin_extras + deprecated_extra
