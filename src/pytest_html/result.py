import json
import os
import re
import time
import warnings
from base64 import b64decode
from base64 import b64encode
from html import escape
from os.path import isfile

from _pytest.logging import _remove_ansi_escape_sequences
from py.xml import html
from py.xml import raw

from . import extras
from .util import ansi_support


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
        self.max_asset_filename_length = int(config.getini("max_asset_filename_length"))
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

    def create_asset(self, content, extra_index, test_index, file_extension, mode="w"):
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
                href = self._data_uri(content, mime_type=extra.get("mime_type"))
            else:
                href = self.create_asset(
                    content, extra_index, test_index, extra.get("extension")
                )

        elif extra.get("format_type") == extras.FORMAT_TEXT:
            content = extra.get("content")
            if isinstance(content, bytes):
                content = content.decode("utf-8")
            if self.self_contained:
                href = self._data_uri(content)
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

    def _data_uri(self, content, mime_type="text/plain", charset="utf-8"):
        data = b64encode(content.encode(charset)).decode("ascii")
        return f"data:{mime_type};charset={charset};base64,{data}"
