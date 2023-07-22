# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import warnings
from collections import defaultdict

from pytest_html.util import _handle_ansi


class ReportData:
    def __init__(self, config):
        self._config = config

        default_headers = [
            '<th class="sortable" data-column-type="result">Result</th>',
            '<th class="sortable" data-column-type="testId">Test</th>',
            '<th class="sortable" data-column-type="duration">Duration</th>',
            "<th>Links</th>",
        ]

        self._data = {
            "title": "",
            "collectedItems": 0,
            "totalDuration": {
                "total": 0,
                "formatted": "",
            },
            "runningState": "not_started",
            "environment": {},
            "tests": defaultdict(list),
            "additionalSummary": defaultdict(list),
            "resultsTableHeader": default_headers,
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

    def add_test(self, test_data, report, logs):
        # regardless of pass or fail we must add teardown logging to "call"
        if report.when == "teardown":
            self.append_teardown_log(report)

        # passed "setup" and "teardown" are not added to the html
        if report.when == "call" or (
            report.when in ["setup", "teardown"] and report.outcome != "passed"
        ):
            test_data["log"] = _handle_ansi("\n".join(logs))
            self._data["tests"][report.nodeid].append(test_data)
            return True

        return False

    def append_teardown_log(self, report):
        log = []
        if self._data["tests"][report.nodeid]:
            # Last index is "call"
            test = self._data["tests"][report.nodeid][-1]
            for section in report.sections:
                header, content = section
                if "teardown" in header:
                    log.append(f"{' ' + header + ' ':-^80}\n{content}")
            test["log"] += _handle_ansi("\n".join(log))
