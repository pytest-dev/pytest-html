# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import datetime
import json
import math
import os
import re
import time
import warnings
from weakref import WeakSet
from collections import defaultdict
from html import escape
from pathlib import Path

import pytest

from pytest_html import __version__
from pytest_html import extras


class BaseReport:
    def __init__(self, report_path, config, report_data, template, css):
        self._report_path = (
            Path.cwd() / Path(os.path.expandvars(report_path)).expanduser()
        )
        self._report_path.parent.mkdir(parents=True, exist_ok=True)
        self._config = config
        self._template = template
        self._css = css
        self._max_asset_filename_length = int(
            config.getini("max_asset_filename_length")
        )

        self._reports = {}
        self._implicit_attempts = defaultdict(int)
        self._completed_attempts = defaultdict(set)
        # Keep report delivery idempotent without retaining every TestReport
        # after its owner has released it. Distinct phase reports may share a
        # nodeid, phase and outcome; only object identity proves a replay.
        self._seen_reports = WeakSet()
        self._report = report_data
        self._report.title = self._report_path.name
        self._suite_start_time = time.time()

    @property
    def css(self):
        # implement in subclasses
        return

    def _asset_filename(self, test_id, extra_index, test_index, file_extension):
        return "{}_{}_{}.{}".format(
            re.sub(r"[^\w.]", "_", test_id),
            str(extra_index),
            str(test_index),
            file_extension,
        )[-self._max_asset_filename_length :]

    def _generate_report(self, self_contained=False):
        generated = datetime.datetime.now()
        test_data = self._report.data
        test_data = json.dumps(test_data)
        rendered_report = self._template.render(
            title=self._report.title,
            date=generated.strftime("%d-%b-%Y"),
            time=generated.strftime("%H:%M:%S"),
            version=__version__,
            styles=self.css,
            run_count=self._run_count(),
            running_state=self._report.running_state,
            self_contained=self_contained,
            outcomes=self._report.outcomes,
            test_data=test_data,
            table_head=self._report.table_header,
            additional_summary=self._report.additional_summary,
        )

        self._write_report(rendered_report)

    def _generate_environment(self):
        try:
            from pytest_metadata.plugin import metadata_key

            metadata = self._config.stash[metadata_key]
        except ImportError:
            # old version of pytest-metadata
            metadata = self._config._metadata
            warnings.warn(
                "'pytest-metadata < 3.0.0' is deprecated and support will be dropped in next major version",
                DeprecationWarning,
            )

        for key in metadata.keys():
            value = metadata[key]
            if self._is_redactable_environment_variable(key):
                black_box_ascii_value = 0x2593
                metadata[key] = "".join(chr(black_box_ascii_value) for _ in str(value))

        return metadata

    def _is_redactable_environment_variable(self, environment_variable):
        redactable_regexes = self._config.getini("environment_table_redact_list")
        for redactable_regex in redactable_regexes:
            if re.match(redactable_regex, environment_variable):
                return True

        return False

    def _data_content(self, *args, **kwargs):
        pass

    def _media_content(self, *args, **kwargs):
        pass

    def _process_extras(self, report, test_id, test_index=None):
        if test_index is None:
            test_index = hasattr(report, "rerun") and report.rerun + 1 or 0
        report_extras = getattr(report, "extras", [])
        for extra_index, extra in enumerate(report_extras):
            content = extra["content"]
            asset_name = self._asset_filename(
                test_id.encode("utf-8").decode("unicode_escape"),
                extra_index,
                test_index,
                extra["extension"],
            )
            if extra["format_type"] == extras.FORMAT_JSON:
                content = json.dumps(content)
                extra["content"] = self._data_content(
                    content, asset_name=asset_name, mime_type=extra["mime_type"]
                )

            if extra["format_type"] == extras.FORMAT_TEXT:
                if isinstance(content, bytes):
                    content = content.decode("utf-8")
                extra["content"] = self._data_content(
                    content, asset_name=asset_name, mime_type=extra["mime_type"]
                )

            if extra["format_type"] in [extras.FORMAT_IMAGE, extras.FORMAT_VIDEO]:
                extra["content"] = self._media_content(
                    content, asset_name=asset_name, mime_type=extra["mime_type"]
                )

        return report_extras

    def _write_report(self, rendered_report):
        with self._report_path.open("w", encoding="utf-8") as f:
            f.write(rendered_report)

    def _run_count(self):
        relevant_outcomes = ["passed", "failed", "xpassed", "xfailed"]
        counts = 0
        for outcome in self._report.outcomes.keys():
            if outcome in relevant_outcomes:
                counts += self._report.outcomes[outcome]["value"]

        plural = counts > 1
        duration = _format_duration(self._report.total_duration)

        if self._report.running_state == "finished":
            return f"{counts} {'tests' if plural else 'test'} took {duration}."

        return f"{counts}/{self._report.collected_items} {'tests' if plural else 'test'} done."

    def _hydrate_data(self, data, cells):
        for index, cell in enumerate(cells):
            # extract column name and data if column is sortable
            if "sortable" in self._report.table_header[index]:
                name_match = re.search(r"col-(\w+)", cell)
                data_match = re.search(r"<td.*?>(.*?)</td>", cell)
                if name_match and data_match:
                    data[name_match.group(1)] = data_match.group(1)

    @pytest.hookimpl(trylast=True)
    def pytest_sessionstart(self, session):
        self._report.set_data("environment", self._generate_environment())

        session.config.hook.pytest_html_report_title(report=self._report)

        headers = self._report.table_header
        session.config.hook.pytest_html_results_table_header(cells=headers)
        self._report.table_header = _fix_py(headers)

        self._report.running_state = "started"
        if self._config.getini("generate_report_on_test"):
            self._generate_report()

    @pytest.hookimpl(trylast=True)
    def pytest_sessionfinish(self, session):
        for nodeid in list(self._reports):
            self._finalize_attempt(nodeid)
        session.config.hook.pytest_html_results_summary(
            prefix=self._report.additional_summary["prefix"],
            summary=self._report.additional_summary["summary"],
            postfix=self._report.additional_summary["postfix"],
            session=session,
        )
        self._report.running_state = "finished"
        suite_stop_time = time.time()
        self._report.total_duration = suite_stop_time - self._suite_start_time
        self._generate_report()

    @pytest.hookimpl(trylast=True)
    def pytest_terminal_summary(self, terminalreporter):
        terminalreporter.write_sep(
            "-",
            f"Generated html report: {self._report_path.as_uri()}",
        )

    @pytest.hookimpl(trylast=True)
    def pytest_collectreport(self, report):
        if report.failed:
            self._process_report(report, 0, [])

    @pytest.hookimpl(trylast=True)
    def pytest_collection_finish(self, session):
        self._report.collected_items = len(session.items)

    @pytest.hookimpl(trylast=True)
    def pytest_runtest_logreport(self, report):
        if report in self._seen_reports:
            return
        self._seen_reports.add(report)

        if hasattr(report, "duration_formatter"):
            warnings.warn(
                "'duration_formatter' has been removed and no longer has any effect!"
                "Please use the 'pytest_html_duration_format' hook instead.",
                DeprecationWarning,
            )

        nodeid = report.nodeid
        rerun = getattr(report, "rerun", None)
        marker = ("rerun", rerun) if rerun is not None else None
        current = self._reports.get(nodeid)

        if marker is not None and marker in self._completed_attempts[nodeid]:
            return

        if current is not None:
            if marker is not None and current["marker"] != marker:
                if (
                    current["marker"][0] == "implicit"
                    and "call" not in current["phases"]
                ):
                    # The provisional setup belongs to a marked attempt, so
                    # do not consume an unmarked attempt's asset namespace.
                    self._implicit_attempts[nodeid] -= 1
                    current["marker"] = marker
                    current["test_index"] = rerun + 1
                else:
                    self._finalize_attempt(nodeid)
                    current = None
            elif (
                marker is None
                and report.when == "setup"
                and ("call" in current["phases"] or "teardown" in current["phases"])
            ):
                self._finalize_attempt(nodeid)
                current = None

        if current is None:
            if report.when == "teardown" and report.outcome == "passed":
                # With no open attempt, a passed teardown has no visible row
                # to receive extras. Do not consume the next attempt's asset
                # suffix; a separate failed teardown *does* get its own row.
                return
            index = self._implicit_attempts[nodeid]
            if marker is None:
                marker = ("implicit", index)
                test_index = -index
                self._implicit_attempts[nodeid] += 1
            else:
                test_index = rerun + 1
            current = {
                "marker": marker,
                "test_index": test_index,
                "phases": set(),
                "reports": [],
            }
            self._reports[nodeid] = current

        current["reports"].append(report)
        current["phases"].add(report.when)
        if report.when == "teardown":
            self._finalize_attempt(nodeid)

    def _finalize_attempt(self, nodeid):
        attempt = self._reports.pop(nodeid)
        reports = attempt["reports"]
        self._completed_attempts[nodeid].add(attempt["marker"])
        duration = sum(each.duration for each in reports if each.outcome != "rerun")

        def is_visible(each):
            return each.when in ("call", "collect") or (
                each.when in ("setup", "teardown") and each.outcome != "passed"
            )

        visible = [each for each in reports if is_visible(each)]
        recipient = next((each for each in visible if each.when == "call"), None)
        if recipient is None:
            recipient = next((each for each in visible if each.when == "setup"), None)
        if recipient is None:
            recipient = next(
                (each for each in visible if each.when == "teardown"), None
            )

        report_extras = {id(each): [] for each in reports}
        for each in reports:
            target = each if is_visible(each) else recipient
            if target is None:
                continue
            test_id = each.nodeid
            if each.when != "call":
                test_id += f"::{each.when}"
            report_extras[id(target)].extend(
                self._process_extras(each, test_id, attempt["test_index"])
            )

        previous_row = None
        for each in reports:
            report_duration = duration if each.when == "call" else each.duration
            row = self._process_report(
                each, report_duration, report_extras[id(each)], previous_row
            )
            if row is not None:
                previous_row = row

        if self._config.getini("generate_report_on_test"):
            self._generate_report()

    def _process_report(
        self, report, duration, processed_extras, teardown_recipient=None
    ):
        outcome = _process_outcome(report)
        try:
            # hook returns as list for some reason
            formatted_duration = self._config.hook.pytest_html_duration_format(
                duration=duration
            )[0]
        except IndexError:
            formatted_duration = _format_duration(duration)

        test_id = report.nodeid
        if report.when != "call":
            test_id += f"::{report.when}"

        data = {
            "extras": processed_extras,
        }

        links = [
            extra
            for extra in data["extras"]
            if extra["format_type"] in ["json", "text", "url"]
        ]
        cells = [
            f'<td class="col-result">{outcome}</td>',
            f'<td class="col-testId">{test_id}</td>',
            f'<td class="col-duration">{formatted_duration}</td>',
            f'<td class="col-links">{_process_links(links)}</td>',
        ]
        self._config.hook.pytest_html_results_table_row(report=report, cells=cells)
        if not cells:
            return

        cells = _fix_py(cells)
        self._hydrate_data(data, cells)
        data["resultsTableRow"] = cells

        processed_logs = _process_logs(report)
        self._config.hook.pytest_html_results_table_html(
            report=report, data=processed_logs
        )

        return self._report.add_test(
            data, report, outcome, processed_logs, teardown_recipient
        )


def _format_duration(duration):
    if duration < 1:
        return f"{round(duration * 1000)} ms"

    hours = math.floor(duration / 3600)
    remaining_seconds = duration % 3600
    minutes = math.floor(remaining_seconds / 60)
    remaining_seconds = remaining_seconds % 60
    seconds = round(remaining_seconds)

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _is_error(report):
    return (
        report.when in ["setup", "teardown", "collect"] and report.outcome == "failed"
    )


def _process_logs(report):
    log = []
    if report.longreprtext:
        log.append(escape(report.longreprtext) + "\n")
    # Don't add captured output to reruns
    if report.outcome != "rerun":
        for section in report.sections:
            header, content = map(escape, section)
            log.append(f"{' ' + header + ' ':-^80}\n{content}")

            # weird formatting related to logs
            if "log" in header:
                log.append("")
                if "call" in header:
                    log.append("")
    if not log:
        log.append("No log output captured.")
    return log


def _process_outcome(report):
    if _is_error(report):
        return "Error"
    if hasattr(report, "wasxfail"):
        if report.outcome in ["passed", "failed"]:
            return "XPassed"
        if report.outcome == "skipped":
            return "XFailed"

    return report.outcome.capitalize()


def _process_links(links):
    a_tag = '<a target="_blank" href="{content}" class="col-links__extra {format_type}">{name}</a>'
    return "".join([a_tag.format_map(link) for link in links])


def _fix_py(cells):
    # backwards-compat
    new_cells = []
    for html in cells:
        if not isinstance(html, str):
            if html.__module__.startswith("py."):
                warnings.warn(
                    "The 'py' module is deprecated and support "
                    "will be removed in a future release.",
                    DeprecationWarning,
                )
            html = str(html)
            html = html.replace("col=", "data-column-type=")
        new_cells.append(html)
    return new_cells
