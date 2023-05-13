# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import datetime
import json
import os
import re
import warnings
from pathlib import Path

import pytest
from jinja2 import Environment
from jinja2 import FileSystemLoader
from jinja2 import select_autoescape

from pytest_html import __version__
from pytest_html import extras
from pytest_html.table import Header
from pytest_html.table import Row
from pytest_html.util import _ansi_styles
from pytest_html.util import cleanup_unserializable


class BaseReport:
    def __init__(self, report_path, config, report_data, default_css="style.css"):
        self._report_path = Path(os.path.expandvars(report_path)).expanduser()
        self._report_path.parent.mkdir(parents=True, exist_ok=True)
        self._resources_path = Path(__file__).parent.joinpath("resources")
        self._config = config
        self._template = _read_template([self._resources_path])
        self._css = _process_css(
            Path(self._resources_path, default_css), self._config.getoption("css")
        )
        self._max_asset_filename_length = int(
            config.getini("max_asset_filename_length")
        )

        self._report = report_data
        self._report.title = self._report_path.name

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
        rendered_report = self._render_html(
            generated.strftime("%d-%b-%Y"),
            generated.strftime("%H:%M:%S"),
            __version__,
            self.css,
            self_contained=self_contained,
            test_data=cleanup_unserializable(self._report.data),
            prefix=self._report.data["additionalSummary"]["prefix"],
            summary=self._report.data["additionalSummary"]["summary"],
            postfix=self._report.data["additionalSummary"]["postfix"],
        )

        self._write_report(rendered_report)

    def _generate_environment(self):
        metadata = self._config._metadata
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

    def _process_extras(self, report, test_id):
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

    def _render_html(
        self,
        date,
        time,
        version,
        styles,
        self_contained,
        test_data,
        summary,
        prefix,
        postfix,
    ):
        return self._template.render(
            date=date,
            time=time,
            version=version,
            styles=styles,
            self_contained=self_contained,
            test_data=json.dumps(test_data),
            summary=summary,
            prefix=prefix,
            postfix=postfix,
        )

    def _write_report(self, rendered_report):
        with self._report_path.open("w", encoding="utf-8") as f:
            f.write(rendered_report)

    @pytest.hookimpl(trylast=True)
    def pytest_sessionstart(self, session):
        config = session.config
        if hasattr(config, "_metadata") and config._metadata:
            self._report.set_data("environment", self._generate_environment())

        session.config.hook.pytest_html_report_title(report=self._report)

        header_cells = Header()
        session.config.hook.pytest_html_results_table_header(cells=header_cells)
        self._report.set_data("resultsTableHeader", header_cells.html)
        self._report.set_data("headerPops", header_cells.get_pops())

        self._report.set_data("runningState", "Started")
        self._generate_report()

    @pytest.hookimpl(trylast=True)
    def pytest_sessionfinish(self, session):
        session.config.hook.pytest_html_results_summary(
            prefix=self._report.data["additionalSummary"]["prefix"],
            summary=self._report.data["additionalSummary"]["summary"],
            postfix=self._report.data["additionalSummary"]["postfix"],
            session=session,
        )
        self._report.set_data("runningState", "Finished")
        self._generate_report()

    @pytest.hookimpl(trylast=True)
    def pytest_terminal_summary(self, terminalreporter):
        terminalreporter.write_sep(
            "-", f"Generated html report: file://{self._report_path.resolve()}"
        )

    @pytest.hookimpl(trylast=True)
    def pytest_collection_finish(self, session):
        self._report.set_data("collectedItems", len(session.items))

    @pytest.hookimpl(trylast=True)
    def pytest_runtest_logreport(self, report):
        if hasattr(report, "duration_formatter"):
            warnings.warn(
                "'duration_formatter' has been removed and no longer has any effect!",
                DeprecationWarning,
            )

        data = {
            "duration": report.duration,
        }

        test_id = report.nodeid
        if report.when != "call":
            test_id += f"::{report.when}"
        data["testId"] = test_id

        row_cells = Row()
        self._config.hook.pytest_html_results_table_row(report=report, cells=row_cells)
        if row_cells.html is None:
            return
        data["resultsTableRow"] = row_cells.html
        for sortable, value in row_cells.sortables.items():
            data[sortable] = value

        processed_logs = _process_logs(report)
        self._config.hook.pytest_html_results_table_html(
            report=report, data=processed_logs
        )

        data["result"] = _process_outcome(report)
        data["extras"] = self._process_extras(report, test_id)

        if self._report.add_test(data, report, processed_logs):
            self._generate_report()


def _process_css(default_css, extra_css):
    with open(default_css, encoding="utf-8") as f:
        css = f.read()

    # Add user-provided CSS
    for path in extra_css:
        css += "\n/******************************"
        css += "\n * CUSTOM CSS"
        css += f"\n * {path}"
        css += "\n ******************************/\n\n"
        with open(path, encoding="utf-8") as f:
            css += f.read()

    # ANSI support
    if _ansi_styles:
        ansi_css = [
            "\n/******************************",
            " * ANSI2HTML STYLES",
            " ******************************/\n",
        ]
        ansi_css.extend([str(r) for r in _ansi_styles])
        css += "\n".join(ansi_css)

    return css


def _is_error(report):
    return report.when in ["setup", "teardown"] and report.outcome == "failed"


def _process_logs(report):
    log = []
    if report.longreprtext:
        log.append(report.longreprtext.replace("<", "&lt;").replace(">", "&gt;") + "\n")
    for section in report.sections:
        header, content = section
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


def _read_template(search_paths, template_name="index.jinja2"):
    env = Environment(
        loader=FileSystemLoader(search_paths),
        autoescape=select_autoescape(
            enabled_extensions=("jinja2",),
        ),
    )
    return env.get_template(template_name)
