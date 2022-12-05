import bisect
import datetime
import json
import os
import re
import time
from collections import defaultdict
from collections import OrderedDict
from pathlib import Path

from jinja2 import Environment
from jinja2 import FileSystemLoader
from markupsafe import escape
from markupsafe import Markup

from . import __pypi_url__
from . import __version__
from .outcome import Outcome
from .result import TestResult
from .result_header import ResultHeader
from .util import ansi_support


class HTMLReport:
    def __init__(self, logfile, config):
        logfile = Path(os.path.expandvars(logfile)).expanduser()
        self.logfile = logfile.absolute()
        self.title = self.logfile.name
        self.results = []
        self.errors = self.failed = 0
        self.passed = self.skipped = 0
        self.xfailed = self.xpassed = 0
        has_rerun = config.pluginmanager.hasplugin("rerunfailures")
        self.rerun = 0 if has_rerun else None
        self.self_contained = config.getoption("self_contained_html")
        self.config = config
        self.reports = defaultdict(list)
        self.jinja = Environment(
            loader=FileSystemLoader(Path(__file__).parent / "resources"),
            autoescape=True,
        )

    def _appendrow(self, outcome, report):
        result = TestResult(outcome, report, self.jinja, self.logfile, self.config)
        if result.cells:
            index = bisect.bisect_right(self.results, result)
            self.results.insert(index, result)

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
        report_tmpl = self.jinja.get_template("report.html.jinja")
        main_js_path = Path(__file__).parent / "resources" / "main.js"
        main_js = main_js_path.read_text()
        css_path = Path(__file__).parent / "resources" / "style.css"
        self.style_css = css_path.read_text()
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
            self.style_css += Path(path).read_text()
        session.config.hook.pytest_html_report_title(report=self)
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
        summary_prefix, summary_postfix = [], []
        session.config.hook.pytest_html_results_summary(
            prefix=summary_prefix, summary=outcomes, postfix=summary_postfix
        )
        headers = [
            ResultHeader(
                label="Result", class_html="sortable result initial-sort", col="result"
            ),
            ResultHeader(label="Test", class_html="sortable", col="name"),
            ResultHeader(label="Duration", class_html="sortable", col="duration"),
            ResultHeader(label="Links", class_html="sortable links", col="links"),
        ]
        session.config.hook.pytest_html_results_table_header(cells=headers)
        unicode_doc = report_tmpl.render(
            version=__version__,
            pypi_url=__pypi_url__,
            generated=generated,
            title=self.title,
            css_embedded=self.self_contained,
            css_content=self.style_css,
            js_content=main_js,
            environments=self._generate_environment(session.config),
            dumps_order=self._dumps_order,
            numtests=numtests,
            suite_time_delta=suite_time_delta,
            summary_prefix=summary_prefix,
            summary_postfix=summary_postfix,
            headers=headers,
            outcomes=outcomes,
            results=[str(result) for result in self.results],
        )
        # Fix encoding issues, e.g. with surrogates
        unicode_doc = unicode_doc.encode("utf-8", errors="xmlcharrefreplace")
        return unicode_doc.decode("utf-8")

    def _generate_environment(self, config):
        if not hasattr(config, "_metadata") or config._metadata is None:
            return []
        metadata = config._metadata
        environments = {}
        keys = [k for k in metadata.keys()]
        if not isinstance(metadata, OrderedDict):
            keys.sort()
        for key in keys:
            value = metadata[key]
            if self._is_redactable_environment_variable(key, config):
                black_box_ascii_value = 0x2593
                value = "".join(chr(black_box_ascii_value) for char in str(value))
            environments[key] = value
        return environments

    def _is_redactable_environment_variable(self, environment_variable, config):
        redactable_regexes = config.getini("environment_table_redact_list")
        for redactable_regex in redactable_regexes:
            if re.match(redactable_regex, environment_variable):
                return True

        return False

    def _dumps_order(self, value):
        sorted_dict = {
            escape(k): escape(value[k]) if isinstance(value[k], str) else value[k]
            for k in sorted(value)
        }
        return Markup(json.dumps(sorted_dict))

    def _save_report(self, report_content):
        dir_name = self.logfile.parent
        assets_dir = dir_name / "assets"

        dir_name.mkdir(parents=True, exist_ok=True)
        if not self.self_contained:
            assets_dir.mkdir(parents=True, exist_ok=True)

        self.logfile.write_text(report_content)
        if not self.self_contained:
            style_path = assets_dir / "style.css"
            style_path.write_text(self.style_css)

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
        terminalreporter.write_sep("-", f"generated html file: {self.logfile.as_uri()}")
