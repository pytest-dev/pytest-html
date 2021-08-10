import bisect
import datetime
import json
import os
import re
import time
from collections import OrderedDict, defaultdict
from copy import deepcopy

from py.xml import html
from py.xml import raw

from . import __pypi_url__
from . import __version__
from .outcome import Outcome
from .result import TestResult
from .util import ansi_support


class HTMLReport:
    def __init__(self, logfile, config):
        logfile = os.path.expanduser(os.path.expandvars(logfile))
        self.logfile = os.path.abspath(logfile)
        self.test_logs = defaultdict(list)
        self.results = defaultdict(list)
        self.test_logs_keys = []
        self.title = os.path.basename(self.logfile)
        self.errors = self.failed = 0
        self.passed = self.skipped = 0
        self.xfailed = self.xpassed = 0
        has_rerun = config.pluginmanager.hasplugin("rerunfailures")
        self.rerun = 0 if has_rerun else None
        self.self_contained = config.getoption("self_contained_html")
        self.config = config
        self.reports = defaultdict(list)
        self.extra_sections = []

    def _appendrow(self, outcome, report):
        result = TestResult(outcome, report, self.logfile, self.config)
        if result.row_table is not None:
            group = getattr(report, 'group', None)

            if group not in self.results:
                self.test_logs_keys.append(group)

            index = bisect.bisect_right(self.results[group], result)
            self.results[group].insert(index, result)
            tbody = html.tbody(
                result.row_table,
                class_="{} results-table-row".format(result.outcome.lower()),
            )
            if result.row_extra is not None:
                tbody.append(result.row_extra)
            self.test_logs[group].insert(index, tbody)

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

    def add_section(self, data):
        self.extra_sections.append(data)

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

        session.config.hook.pytest_html_report_title(report=self)

        head = html.head(html.meta(charset="utf-8"), html.title(self.title), html_css)

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

        # Create each section of the HTML report
        sections = []

        #
        # Header
        #

        header = [
            html.h1(self.title),
            html.p(
                "Report generated on {} at {} by ".format(
                    generated.strftime("%d-%b-%Y"), generated.strftime("%H:%M:%S")
                ),
                html.a("pytest-html", href=__pypi_url__),
                f" v{__version__}",
            )
        ]
        sections.append(header)
        session.config.hook.pytest_html_modify_section(name='header', data=header)

        #
        # Environment
        #

        environment = self._generate_environment(session.config)
        sections.append(environment)
        session.config.hook.pytest_html_modify_section(name='environment', data=environment)

        #
        # Summary
        #

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

        summary_prefix, summary_postfix = [], []
        session.config.hook.pytest_html_results_summary(
            prefix=summary_prefix, summary=summary, postfix=summary_postfix
        )

        summary = [html.h2("Summary")] + summary_prefix + summary + summary_postfix
        sections.append(summary)
        session.config.hook.pytest_html_modify_section(name='summary', data=summary)

        #
        # Results
        #

        cells = [
            html.th("Result", class_="sortable result initial-sort", col="result"),
            html.th("Test", class_="sortable", col="name"),
            html.th("Duration", class_="sortable", col="duration"),
            html.th("Links", class_="sortable links", col="links"),
        ]
        session.config.hook.pytest_html_results_table_header(cells=cells)

        results = [html.h2("Results")]
        for group in self.test_logs_keys:
            results += [
                html.h3(group),
                html.table(
                    [
                        html.thead(
                            html.tr(deepcopy(cells)),
                            html.tr(
                                [
                                    html.th(
                                        "No results found. Try to check the filters",
                                        colspan=len(cells),
                                    )
                                ],
                                class_="not-found-message",
                                hidden="true",
                            ),
                            class_="results-table-head",
                        ),
                        self.test_logs[group],
                    ],
                    class_="results-table",
                )

            ]

        sections.append(results)
        session.config.hook.pytest_html_modify_section(name='results', data=results)

        sections += self.extra_sections

        # Put sections together to create the HTML document.
        with open(
            os.path.join(os.path.dirname(__file__), "resources", "main.js")
        ) as main_js_fp:
            main_js = main_js_fp.read()

        body = html.body(html.script(raw(main_js)), onLoad="init()")

        # Give user chance to arbitrarily modify sections
        session.config.hook.pytest_html_modify_all_sections(sections=sections)

        for section in sections:
            body.extend(section)

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
            if self._is_redactable_environment_variable(key, config):
                black_box_ascii_value = 0x2593
                value = "".join(chr(black_box_ascii_value) for char in str(value))

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

    def _is_redactable_environment_variable(self, environment_variable, config):
        redactable_regexes = config.getini("environment_table_redact_list")
        for redactable_regex in redactable_regexes:
            if re.match(redactable_regex, environment_variable):
                return True

        return False

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
            report_outcome = "passed"
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
                        and report_outcome == "passed"
                    ):
                        report_outcome = test_report.outcome
                        failure_when = test_report.when

                    if hasattr(test_report, "wasxfail"):
                        wasxfail = True

            # the following test_report.<X> = settings come at the end of us
            #  looping through all test_reports that make up a single
            #    case.

            # outcome on the right comes from the outcome of the various
            #  test_reports that make up this test case
            #    we are just carrying it over to the final report.
            test_report.outcome = report_outcome
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
