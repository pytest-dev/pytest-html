# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import bisect
import datetime
import importlib
import json
import os
import re
import time
import warnings
from base64 import b64decode
from base64 import b64encode
from collections import defaultdict
from collections import OrderedDict
from functools import lru_cache
from html import escape
from os.path import isfile

import pytest
from _pytest.logging import _remove_ansi_escape_sequences
from py.xml import html
from py.xml import raw

from . import __pypi_url__
from . import __version__
from . import extras


@lru_cache()
def ansi_support():
    try:
        # from ansi2html import Ansi2HTMLConverter, style  # NOQA
        return importlib.import_module("ansi2html")
    except ImportError:
        # ansi2html is not installed
        pass


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


def pytest_configure(config):
    htmlpath = config.getoption("htmlpath")
    if htmlpath:
        missing_css_files = []
        for csspath in config.getoption("css"):
            if not os.path.exists(csspath):
                missing_css_files.append(csspath)

        if missing_css_files:
            oserror = (
                f"Missing CSS file{'s' if len(missing_css_files) > 1 else ''}:"
                f" {', '.join(missing_css_files)}"
            )
            raise OSError(oserror)

        if not hasattr(config, "workerinput"):
            # prevent opening htmlpath on worker nodes (xdist)
            config._html = HTMLReport(htmlpath, config)
            config.pluginmanager.register(config._html)


def pytest_unconfigure(config):
    html = getattr(config, "_html", None)
    if html:
        del config._html
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
            extra.append(pytest_html.extras.url("http://www.example.com/"))
    """
    pytestconfig.extras = []
    yield pytestconfig.extras
    del pytestconfig.extras[:]


def data_uri(content, mime_type="text/plain", charset="utf-8"):
    data = b64encode(content.encode(charset)).decode("ascii")
    return f"data:{mime_type};charset={charset};base64,{data}"


class HTMLReport:
    def __init__(self, logfile, config):
        logfile = os.path.expanduser(os.path.expandvars(logfile))
        self.logfile = os.path.abspath(logfile)
        self.test_logs = []
        self.title = os.path.basename(self.logfile)
        self.results = []
        self.errors = self.failed = 0
        self.passed = self.skipped = 0
        self.xfailed = self.xpassed = 0
        has_rerun = config.pluginmanager.hasplugin("rerunfailures")
        self.rerun = 0 if has_rerun else None
        self.self_contained = config.getoption("self_contained_html")
        self.config = config
        self.reports = defaultdict(list)

    class TestResult:
        def __init__(self, outcome, report, logfile, config):
            self.test_id = report.nodeid.encode("utf-8").decode("unicode_escape")
            if getattr(report, "when", "call") != "call":
                self.test_id = "::".join([report.nodeid, report.when])
            self.time = getattr(report, "duration", 0.0)
            self.formatted_time = self._format_time(report)
            self.outcome = outcome
            self.additional_html = []
            self.links_html = []
            self.self_contained = config.getoption("self_contained_html")
            self.max_asset_filename_length = int(
                config.getini("max_asset_filename_length")
            )
            self.logfile = logfile
            self.config = config
            self.row_table = self.row_extra = None

            test_index = hasattr(report, "rerun") and report.rerun + 1 or 0

            for extra_index, extra in enumerate(getattr(report, "extra", [])):
                self.append_extra_html(extra, extra_index, test_index)

            self.append_log_html(
                report,
                self.additional_html,
                config.option.capture,
                config.option.showcapture,
            )

            cells = [
                html.td(self.outcome, class_="col-result"),
                html.td(self.test_id, class_="col-name"),
                html.td(self.formatted_time, class_="col-duration"),
                html.td(self.links_html, class_="col-links"),
            ]

            self.config.hook.pytest_html_results_table_row(report=report, cells=cells)

            self.config.hook.pytest_html_results_table_html(
                report=report, data=self.additional_html
            )

            if len(cells) > 0:
                tr_class = None
                if self.config.getini("render_collapsed"):
                    tr_class = "collapsed"
                self.row_table = html.tr(cells)
                self.row_extra = html.tr(
                    html.td(self.additional_html, class_="extra", colspan=len(cells)),
                    class_=tr_class,
                )

        def __lt__(self, other):
            order = (
                "Error",
                "Failed",
                "Rerun",
                "XFailed",
                "XPassed",
                "Skipped",
                "Passed",
            )
            return order.index(self.outcome) < order.index(other.outcome)

        def create_asset(
            self, content, extra_index, test_index, file_extension, mode="w"
        ):
            asset_file_name = "{}_{}_{}.{}".format(
                re.sub(r"[^\w\.]", "_", self.test_id),
                str(extra_index),
                str(test_index),
                file_extension,
            )[-self.max_asset_filename_length :]
            asset_path = os.path.join(
                os.path.dirname(self.logfile), "assets", asset_file_name
            )

            os.makedirs(os.path.dirname(asset_path), exist_ok=True)

            relative_path = f"assets/{asset_file_name}"

            kwargs = {"encoding": "utf-8"} if "b" not in mode else {}
            with open(asset_path, mode, **kwargs) as f:
                f.write(content)
            return relative_path

        def append_extra_html(self, extra, extra_index, test_index):
            href = None
            if extra.get("format_type") == extras.FORMAT_IMAGE:
                self._append_image(extra, extra_index, test_index)

            elif extra.get("format_type") == extras.FORMAT_HTML:
                self.additional_html.append(html.div(raw(extra.get("content"))))

            elif extra.get("format_type") == extras.FORMAT_JSON:
                content = json.dumps(extra.get("content"))
                if self.self_contained:
                    href = data_uri(content, mime_type=extra.get("mime_type"))
                else:
                    href = self.create_asset(
                        content, extra_index, test_index, extra.get("extension")
                    )

            elif extra.get("format_type") == extras.FORMAT_TEXT:
                content = extra.get("content")
                if isinstance(content, bytes):
                    content = content.decode("utf-8")
                if self.self_contained:
                    href = data_uri(content)
                else:
                    href = self.create_asset(
                        content, extra_index, test_index, extra.get("extension")
                    )

            elif extra.get("format_type") == extras.FORMAT_URL:
                href = extra.get("content")

            elif extra.get("format_type") == extras.FORMAT_VIDEO:
                self._append_video(extra, extra_index, test_index)

            if href is not None:
                self.links_html.append(
                    html.a(
                        extra.get("name"),
                        class_=extra.get("format_type"),
                        href=href,
                        target="_blank",
                    )
                )
                self.links_html.append(" ")

        def _format_time(self, report):
            # parse the report duration into its display version and return
            # it to the caller
            duration = getattr(report, "duration", None)
            if duration is None:
                return ""

            duration_formatter = getattr(report, "duration_formatter", None)
            string_duration = str(duration)
            if duration_formatter is None:
                if "." in string_duration:
                    split_duration = string_duration.split(".")
                    split_duration[1] = split_duration[1][0:2]

                    string_duration = ".".join(split_duration)

                return string_duration
            else:
                # support %f, since time.strftime doesn't support it out of the box
                # keep a precision of 2 for legacy reasons
                formatted_milliseconds = "00"
                if "." in string_duration:
                    milliseconds = string_duration.split(".")[1]
                    formatted_milliseconds = milliseconds[0:2]

                duration_formatter = duration_formatter.replace(
                    "%f", formatted_milliseconds
                )
                duration_as_gmtime = time.gmtime(report.duration)
                return time.strftime(duration_formatter, duration_as_gmtime)

        def _populate_html_log_div(self, log, report):
            if report.longrepr:
                # longreprtext is only filled out on failure by pytest
                #    otherwise will be None.
                #  Use full_text if longreprtext is None-ish
                #   we added full_text elsewhere in this file.
                text = report.longreprtext or report.full_text
                for line in text.splitlines():
                    separator = line.startswith("_ " * 10)
                    if separator:
                        log.append(line[:80])
                    else:
                        exception = line.startswith("E   ")
                        if exception:
                            log.append(html.span(raw(escape(line)), class_="error"))
                        else:
                            log.append(raw(escape(line)))
                    log.append(html.br())

            for section in report.sections:
                header, content = map(escape, section)
                log.append(f" {header:-^80} ")
                log.append(html.br())

                if ansi_support():
                    converter = ansi_support().Ansi2HTMLConverter(
                        inline=False, escaped=False
                    )
                    content = converter.convert(content, full=False)
                else:
                    content = _remove_ansi_escape_sequences(content)

                log.append(raw(content))
                log.append(html.br())

        def append_log_html(
            self,
            report,
            additional_html,
            pytest_capture_value,
            pytest_show_capture_value,
        ):
            log = html.div(class_="log")

            should_skip_captured_output = pytest_capture_value == "no"
            if report.outcome == "failed" and not should_skip_captured_output:
                should_skip_captured_output = pytest_show_capture_value == "no"
            if not should_skip_captured_output:
                self._populate_html_log_div(log, report)

            if len(log) == 0:
                log = html.div(class_="empty log")
                log.append("No log output captured.")

            additional_html.append(log)

        def _make_media_html_div(
            self, extra, extra_index, test_index, base_extra_string, base_extra_class
        ):
            content = extra.get("content")
            try:
                is_uri_or_path = content.startswith(("file", "http")) or isfile(content)
            except ValueError:
                # On Windows, os.path.isfile throws this exception when
                # passed a b64 encoded image.
                is_uri_or_path = False
            if is_uri_or_path:
                if self.self_contained:
                    warnings.warn(
                        "Self-contained HTML report "
                        "includes link to external "
                        f"resource: {content}"
                    )

                html_div = html.a(
                    raw(base_extra_string.format(extra.get("content"))), href=content
                )
            elif self.self_contained:
                src = f"data:{extra.get('mime_type')};base64,{content}"
                html_div = raw(base_extra_string.format(src))
            else:
                content = b64decode(content.encode("utf-8"))
                href = src = self.create_asset(
                    content, extra_index, test_index, extra.get("extension"), "wb"
                )
                html_div = html.a(
                    raw(base_extra_string.format(src)),
                    class_=base_extra_class,
                    target="_blank",
                    href=href,
                )
            return html_div

        def _append_image(self, extra, extra_index, test_index):
            image_base = '<img src="{}"/>'
            html_div = self._make_media_html_div(
                extra, extra_index, test_index, image_base, "image"
            )
            self.additional_html.append(html.div(html_div, class_="image"))

        def _append_video(self, extra, extra_index, test_index):
            video_base = '<video controls><source src="{}" type="video/mp4"></video>'
            html_div = self._make_media_html_div(
                extra, extra_index, test_index, video_base, "video"
            )
            self.additional_html.append(html.div(html_div, class_="video"))

    def _appendrow(self, outcome, report):
        result = self.TestResult(outcome, report, self.logfile, self.config)
        if result.row_table is not None:
            index = bisect.bisect_right(self.results, result)
            self.results.insert(index, result)
            tbody = html.tbody(
                result.row_table,
                class_="{} results-table-row".format(result.outcome.lower()),
            )
            if result.row_extra is not None:
                tbody.append(result.row_extra)
            self.test_logs.insert(index, tbody)

    def append_passed(self, report):
        if report.when == "call":
            if hasattr(report, "wasxfail"):
                self.xpassed += 1
                self._appendrow("XPassed", report)
            else:
                self.passed += 1
                self._appendrow("Passed", report)

    def append_failed(self, report):
        if getattr(report, "when", None) == "call":
            if hasattr(report, "wasxfail"):
                # pytest < 3.0 marked xpasses as failures
                self.xpassed += 1
                self._appendrow("XPassed", report)
            else:
                self.failed += 1
                self._appendrow("Failed", report)
        else:
            self.errors += 1
            self._appendrow("Error", report)

    def append_rerun(self, report):
        self.rerun += 1
        self._appendrow("Rerun", report)

    def append_skipped(self, report):
        if hasattr(report, "wasxfail"):
            self.xfailed += 1
            self._appendrow("XFailed", report)
        else:
            self.skipped += 1
            self._appendrow("Skipped", report)

    def _generate_report(self, session):
        suite_stop_time = time.time()
        suite_time_delta = suite_stop_time - self.suite_start_time
        numtests = self.passed + self.failed + self.xpassed + self.xfailed
        generated = datetime.datetime.now()

        with open(
            os.path.join(os.path.dirname(__file__), "resources", "style.css")
        ) as style_css_fp:
            self.style_css = style_css_fp.read()

        if ansi_support():
            ansi_css = [
                "\n/******************************",
                " * ANSI2HTML STYLES",
                " ******************************/\n",
            ]
            ansi_css.extend([str(r) for r in ansi_support().style.get_styles()])
            self.style_css += "\n".join(ansi_css)

        # <DF> Add user-provided CSS
        for path in self.config.getoption("css"):
            self.style_css += "\n/******************************"
            self.style_css += "\n * CUSTOM CSS"
            self.style_css += f"\n * {path}"
            self.style_css += "\n ******************************/\n\n"
            with open(path) as f:
                self.style_css += f.read()

        css_href = "assets/style.css"
        html_css = html.link(href=css_href, rel="stylesheet", type="text/css")
        if self.self_contained:
            html_css = html.style(raw(self.style_css))

        head = html.head(
            html.meta(charset="utf-8"), html.title("Test Report"), html_css
        )

        class Outcome:
            def __init__(
                self, outcome, total=0, label=None, test_result=None, class_html=None
            ):
                self.outcome = outcome
                self.label = label or outcome
                self.class_html = class_html or outcome
                self.total = total
                self.test_result = test_result or outcome

                self.generate_checkbox()
                self.generate_summary_item()

            def generate_checkbox(self):
                checkbox_kwargs = {"data-test-result": self.test_result.lower()}
                if self.total == 0:
                    checkbox_kwargs["disabled"] = "true"

                self.checkbox = html.input(
                    type="checkbox",
                    checked="true",
                    onChange="filterTable(this)",
                    name="filter_checkbox",
                    class_="filter",
                    hidden="true",
                    **checkbox_kwargs,
                )

            def generate_summary_item(self):
                self.summary_item = html.span(
                    f"{self.total} {self.label}", class_=self.class_html
                )

        outcomes = [
            Outcome("passed", self.passed),
            Outcome("skipped", self.skipped),
            Outcome("failed", self.failed),
            Outcome("error", self.errors, label="errors"),
            Outcome("xfailed", self.xfailed, label="expected failures"),
            Outcome("xpassed", self.xpassed, label="unexpected passes"),
        ]

        if self.rerun is not None:
            outcomes.append(Outcome("rerun", self.rerun))

        summary = [
            html.p(f"{numtests} tests ran in {suite_time_delta:.2f} seconds. "),
            html.p(
                "(Un)check the boxes to filter the results.",
                class_="filter",
                hidden="true",
            ),
        ]

        for i, outcome in enumerate(outcomes, start=1):
            summary.append(outcome.checkbox)
            summary.append(outcome.summary_item)
            if i < len(outcomes):
                summary.append(", ")

        cells = [
            html.th("Result", class_="sortable result initial-sort", col="result"),
            html.th("Test", class_="sortable", col="name"),
            html.th("Duration", class_="sortable", col="duration"),
            html.th("Links", class_="sortable links", col="links"),
        ]
        session.config.hook.pytest_html_results_table_header(cells=cells)

        results = [
            html.h2("Results"),
            html.table(
                [
                    html.thead(
                        html.tr(cells),
                        html.tr(
                            [
                                html.th(
                                    "No results found. Try to check the filters",
                                    colspan=len(cells),
                                )
                            ],
                            id="not-found-message",
                            hidden="true",
                        ),
                        id="results-table-head",
                    ),
                    self.test_logs,
                ],
                id="results-table",
            ),
        ]

        with open(
            os.path.join(os.path.dirname(__file__), "resources", "main.js")
        ) as main_js_fp:
            main_js = main_js_fp.read()

        session.config.hook.pytest_html_report_title(report=self)

        body = html.body(
            html.script(raw(main_js)),
            html.h1(self.title),
            html.p(
                "Report generated on {} at {} by ".format(
                    generated.strftime("%d-%b-%Y"), generated.strftime("%H:%M:%S")
                ),
                html.a("pytest-html", href=__pypi_url__),
                f" v{__version__}",
            ),
            onLoad="init()",
        )

        body.extend(self._generate_environment(session.config))

        summary_prefix, summary_postfix = [], []
        session.config.hook.pytest_html_results_summary(
            prefix=summary_prefix, summary=summary, postfix=summary_postfix
        )
        body.extend([html.h2("Summary")] + summary_prefix + summary + summary_postfix)

        body.extend(results)

        doc = html.html(head, body)

        unicode_doc = "<!DOCTYPE html>\n{}".format(doc.unicode(indent=2))

        # Fix encoding issues, e.g. with surrogates
        unicode_doc = unicode_doc.encode("utf-8", errors="xmlcharrefreplace")
        return unicode_doc.decode("utf-8")

    def _generate_environment(self, config):
        if not hasattr(config, "_metadata") or config._metadata is None:
            return []

        metadata = config._metadata
        environment = [html.h2("Environment")]
        rows = []

        keys = [k for k in metadata.keys()]
        if not isinstance(metadata, OrderedDict):
            keys.sort()

        for key in keys:
            value = metadata[key]
            if isinstance(value, str) and value.startswith("http"):
                value = html.a(value, href=value, target="_blank")
            elif isinstance(value, (list, tuple, set)):
                value = ", ".join(str(i) for i in sorted(map(str, value)))
            elif isinstance(value, dict):
                sorted_dict = {k: value[k] for k in sorted(value)}
                value = json.dumps(sorted_dict)
            raw_value_string = raw(str(value))
            rows.append(html.tr(html.td(key), html.td(raw_value_string)))

        environment.append(html.table(rows, id="environment"))
        return environment

    def _save_report(self, report_content):
        dir_name = os.path.dirname(self.logfile)
        assets_dir = os.path.join(dir_name, "assets")

        os.makedirs(dir_name, exist_ok=True)
        if not self.self_contained:
            os.makedirs(assets_dir, exist_ok=True)

        with open(self.logfile, "w", encoding="utf-8") as f:
            f.write(report_content)
        if not self.self_contained:
            style_path = os.path.join(assets_dir, "style.css")
            with open(style_path, "w", encoding="utf-8") as f:
                f.write(self.style_css)

    def _post_process_reports(self):
        for test_name, test_reports in self.reports.items():
            outcome = "passed"
            wasxfail = False
            failure_when = None
            full_text = ""
            extras = []
            duration = 0.0

            # in theory the last one should have all logs so we just go
            #  through them all to figure out the outcome, xfail, duration,
            #    extras, and when it swapped from pass
            for test_report in test_reports:
                if test_report.outcome == "rerun":
                    # reruns are separate test runs for all intensive purposes
                    self.append_rerun(test_report)
                else:
                    full_text += test_report.longreprtext
                    extras.extend(getattr(test_report, "extra", []))
                    duration += getattr(test_report, "duration", 0.0)

                    if (
                        test_report.outcome not in ("passed", "rerun")
                        and outcome == "passed"
                    ):
                        outcome = test_report.outcome
                        failure_when = test_report.when

                    if hasattr(test_report, "wasxfail"):
                        wasxfail = True

            # the following test_report.<X> = settings come at the end of us
            #  looping through all test_reports that make up a single
            #    case.

            # outcome on the right comes from the outcome of the various
            #  test_reports that make up this test case
            #    we are just carrying it over to the final report.
            test_report.outcome = outcome
            test_report.when = "call"
            test_report.nodeid = test_name
            test_report.longrepr = full_text
            test_report.extra = extras
            test_report.duration = duration

            if wasxfail:
                test_report.wasxfail = True

            if test_report.outcome == "passed":
                self.append_passed(test_report)
            elif test_report.outcome == "skipped":
                self.append_skipped(test_report)
            elif test_report.outcome == "failed":
                test_report.when = failure_when
                self.append_failed(test_report)

    def pytest_runtest_logreport(self, report):
        self.reports[report.nodeid].append(report)

    def pytest_collectreport(self, report):
        if report.failed:
            self.append_failed(report)

    def pytest_sessionstart(self, session):
        self.suite_start_time = time.time()

    def pytest_sessionfinish(self, session):
        self._post_process_reports()
        report_content = self._generate_report(session)
        self._save_report(report_content)

    def pytest_terminal_summary(self, terminalreporter):
        terminalreporter.write_sep("-", f"generated html file: file://{self.logfile}")
