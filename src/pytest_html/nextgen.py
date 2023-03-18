import base64
import binascii
import datetime
import json
import os
import re
import warnings
from collections import defaultdict
from functools import partial
from pathlib import Path

import pytest
from jinja2 import Environment
from jinja2 import FileSystemLoader
from jinja2 import select_autoescape

from . import __version__
from . import extras
from .util import cleanup_unserializable


try:
    from ansi2html import Ansi2HTMLConverter, style

    converter = Ansi2HTMLConverter(inline=False, escaped=False)
    _handle_ansi = partial(converter.convert, full=False)
    _ansi_styles = style.get_styles()
except ImportError:
    from _pytest.logging import _remove_ansi_escape_sequences

    _handle_ansi = _remove_ansi_escape_sequences
    _ansi_styles = []


class BaseReport:
    class Cells:
        def __init__(self):
            self._html = {}

        @property
        def html(self):
            return self._html

        def insert(self, index, html):
            self._html[index] = html

    class Report:
        def __init__(self, title, duration_format):
            self._data = {
                "title": title,
                "collectedItems": 0,
                "runningState": "not_started",
                "durationFormat": duration_format,
                "environment": {},
                "tests": [],
                "resultsTableHeader": {},
                "additionalSummary": defaultdict(list),
            }

        @property
        def data(self):
            return self._data

        def add_test(self, test):
            self._data["tests"].append(test)

        def set_data(self, key, value):
            self._data[key] = value

        @property
        def title(self):
            return self._data["title"]

        @title.setter
        def title(self, title):
            self._data["title"] = title

    def __init__(self, report_path, config, default_css="style.css"):
        self._report_path = Path(os.path.expandvars(report_path)).expanduser()
        self._report_path.parent.mkdir(parents=True, exist_ok=True)
        self._resources_path = Path(__file__).parent.joinpath("resources")
        self._config = config
        self._template = _read_template([self._resources_path])
        self._css = _process_css(
            Path(self._resources_path, default_css), self._config.getoption("css")
        )
        self._duration_format = config.getini("duration_format")
        self._max_asset_filename_length = int(
            config.getini("max_asset_filename_length")
        )
        self._report = self.Report(self._report_path.name, self._duration_format)

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

            if (
                extra["format_type"] == extras.FORMAT_IMAGE
                or extra["format_type"] == extras.FORMAT_VIDEO
            ):
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

        header_cells = self.Cells()
        session.config.hook.pytest_html_results_table_header(cells=header_cells)
        self._report.set_data("resultsTableHeader", header_cells.html)

        self._report.set_data("runningState", "Started")
        self._generate_report()

    @pytest.hookimpl(trylast=True)
    def pytest_sessionfinish(self, session):
        session.config.hook.pytest_html_results_summary(
            prefix=self._report.data["additionalSummary"]["prefix"],
            summary=self._report.data["additionalSummary"]["summary"],
            postfix=self._report.data["additionalSummary"]["postfix"],
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
        data = {
            "duration": report.duration,
            "when": report.when,
        }

        test_id = report.nodeid
        if report.when != "call":
            test_id += f"::{report.when}"
        data["testId"] = test_id

        # Order here matters!
        log = report.longreprtext or report.capstdout or "No log output captured."
        data["log"] = _handle_ansi(log)

        data["result"] = _process_outcome(report)

        row_cells = self.Cells()
        self._config.hook.pytest_html_results_table_row(report=report, cells=row_cells)
        data["resultsTableRow"] = row_cells.html

        table_html = []
        self._config.hook.pytest_html_results_table_html(report=report, data=table_html)
        data["tableHtml"] = table_html

        data["extras"] = self._process_extras(report, test_id)
        self._report.add_test(data)
        self._generate_report()


class NextGenReport(BaseReport):
    def __init__(self, report_path, config):
        super().__init__(report_path, config)
        self._assets_path = Path(self._report_path.parent, "assets")
        self._assets_path.mkdir(parents=True, exist_ok=True)
        self._css_path = Path(self._assets_path, "style.css")

        with self._css_path.open("w", encoding="utf-8") as f:
            f.write(self._css)

    @property
    def css(self):
        # print("woot", Path(self._assets_path.name, "style.css"))
        # print("waat", self._css_path.relative_to(self._report_path.parent))
        return Path(self._assets_path.name, "style.css")

    def _data_content(self, content, asset_name, *args, **kwargs):
        content = content.encode("utf-8")
        return self._write_content(content, asset_name)

    def _media_content(self, content, asset_name, *args, **kwargs):
        try:
            media_data = base64.b64decode(content.encode("utf-8"), validate=True)
            return self._write_content(media_data, asset_name)
        except binascii.Error:
            # if not base64 content, just return as it's a file or link
            return content

    def _write_content(self, content, asset_name):
        content_relative_path = Path(self._assets_path, asset_name)
        content_relative_path.write_bytes(content)
        return str(content_relative_path.relative_to(self._report_path.parent))


class NextGenSelfContainedReport(BaseReport):
    def __init__(self, report_path, config):
        super().__init__(report_path, config)

    @property
    def css(self):
        return self._css

    def _data_content(self, content, mime_type, *args, **kwargs):
        charset = "utf-8"
        data = base64.b64encode(content.encode(charset)).decode(charset)
        return f"data:{mime_type};charset={charset};base64,{data}"

    def _media_content(self, content, mime_type, *args, **kwargs):
        try:
            # test if content is base64
            base64.b64decode(content.encode("utf-8"), validate=True)
            return f"data:{mime_type};base64,{content}"
        except binascii.Error:
            # if not base64, issue warning and just return as it's a file or link
            warnings.warn(
                "Self-contained HTML report "
                "includes link to external "
                f"resource: {content}"
            )
            return content

    def _generate_report(self, *args, **kwargs):
        super()._generate_report(self_contained=True)


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


def _process_outcome(report):
    if report.when in ["setup", "teardown"] and report.outcome == "failed":
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
