# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import warnings
from collections import defaultdict

from pytest_html.util import _handle_ansi


class ReportData:
    def __init__(self, config):
        self._config = config
        self._data = {
            "title": "",
            "collectedItems": 0,
            "runningState": "not_started",
            "environment": {},
            "tests": defaultdict(list),
            "resultsTableHeader": {},
            "additionalSummary": defaultdict(list),
        }

        collapsed = config.getini("render_collapsed")
        if collapsed:
            if collapsed.lower() == "true":
                warnings.warn(
                    "'render_collapsed = True' is deprecated and support "
                    "will be removed in the next major release. "
                    "Please use 'render_collapsed = all' instead.",
                    DeprecationWarning,
                )
            self.set_data(
                "renderCollapsed", [outcome.lower() for outcome in collapsed.split(",")]
            )

    @property
    def title(self):
        return self._data["title"]

    @title.setter
    def title(self, title):
        self._data["title"] = title

    @property
    def config(self):
        return self._config

    @property
    def data(self):
        return self._data

    def set_data(self, key, value):
        self._data[key] = value

    def add_test(self, test_data, report, row, remove_log=False):
        for sortable, value in row.sortables.items():
            test_data[sortable] = value

        # regardless of pass or fail we must add teardown logging to "call"
        if report.when == "teardown" and not remove_log:
            self.update_test_log(report)

        # passed "setup" and "teardown" are not added to the html
        if report.when == "call" or (
            report.when in ["setup", "teardown"] and report.outcome != "passed"
        ):
            if not remove_log:
                processed_logs = _process_logs(report)
                test_data["log"] = _handle_ansi(processed_logs)
            self._data["tests"][report.nodeid].append(test_data)
            return True

        return False

    def update_test_log(self, report):
        log = []
        for test in self._data["tests"][report.nodeid]:
            if test["testId"] == report.nodeid and "log" in test:
                for section in report.sections:
                    header, content = section
                    if "teardown" in header:
                        log.append(f"{' ' + header + ' ':-^80}")
                        log.append(content)
                test["log"] += _handle_ansi("\n".join(log))


def _process_logs(report):
    log = []
    if report.longreprtext:
        log.append(report.longreprtext.replace("<", "&lt;").replace(">", "&gt;") + "\n")
    for section in report.sections:
        header, content = section
        log.append(f"{' ' + header + ' ':-^80}")
        log.append(content)

        # weird formatting related to logs
        if "log" in header:
            log.append("")
            if "call" in header:
                log.append("")
    if not log:
        log.append("No log output captured.")
    return "\n".join(log)
