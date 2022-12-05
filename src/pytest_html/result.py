import json
import re
import time
import warnings
from base64 import b64decode
from base64 import b64encode
from html import escape
from os.path import isfile
from pathlib import Path

from _pytest.logging import _remove_ansi_escape_sequences

from . import extras
from .result_data import ResultData
from .util import ansi_support


class TestResult:
    def __init__(self, outcome, report, jinja, logfile, config):
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
        self.jinja = jinja
        self.logfile = logfile
        self.config = config
        self.render_collapsed = config.getini("render_collapsed")
        test_index = hasattr(report, "rerun") and report.rerun + 1 or 0
        for extra_index, extra in enumerate(getattr(report, "extra", [])):
            self.append_extra_html(extra, extra_index, test_index)
        self.append_log_html(
            report,
            self.additional_html,
            config.option.capture,
            config.option.showcapture,
        )
        self.cells = [
            ResultData(data=self.outcome, name="result"),
            ResultData(data=self.test_id, name="name"),
            ResultData(data=self.formatted_time, name="duration"),
            ResultData(data=" ".join(self.links_html), name="links"),
        ]
        self.config.hook.pytest_html_results_table_row(report=report, cells=self.cells)
        self.config.hook.pytest_html_results_table_html(
            report=report, data=self.additional_html
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
        asset_path = Path(self.logfile).parent / "assets" / asset_file_name

        asset_path.parent.mkdir(exist_ok=True, parents=True)

        relative_path = f"assets/{asset_file_name}"

        kwargs = {"encoding": "utf-8"} if "b" not in mode else {}
        func = asset_path.write_bytes if "b" in mode else asset_path.write_text
        func(content, **kwargs)

        return relative_path

    def append_extra_html(self, extra, extra_index, test_index):
        href = None
        if extra.get("format_type") == extras.FORMAT_IMAGE:
            href = self._append_image(extra, extra_index, test_index)
        elif extra.get("format_type") == extras.FORMAT_HTML:
            href = self._append_html(extra, extra_index, test_index)
        elif extra.get("format_type") == extras.FORMAT_JSON:
            href = self._append_json(extra, extra_index, test_index)
        elif extra.get("format_type") == extras.FORMAT_TEXT:
            href = self._append_text(extra, extra_index, test_index)
        elif extra.get("format_type") == extras.FORMAT_URL:
            href = self._append_url(extra, extra_index, test_index)
        elif extra.get("format_type") == extras.FORMAT_VIDEO:
            href = self._append_video(extra, extra_index, test_index)
        if href is not None:
            self.links_html.append(
                f'<a class="{extra.get("format_type")}" href="{href}" target="_blank">'
                f'{extra.get("name")}</a>'
            )

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

    def _populate_html_log_div(self, report):
        logs = []
        if report.longrepr:
            # longreprtext is only filled out on failure by pytest
            #    otherwise will be None.
            #  Use full_text if longreprtext is None-ish
            #   we added full_text elsewhere in this file.
            text = report.longreprtext or report.full_text
            for line in text.splitlines():
                separator = line.startswith("_ " * 10)
                if separator:
                    logs.append(line[:80])
                else:
                    exception = line.startswith("E   ")
                    if exception:
                        logs.append(f'<span class="error">{escape(line)}</span>')
                    else:
                        logs.append(escape(line))
                logs.append("<br/>")
        for section in report.sections:
            header, content = map(escape, section)
            logs.append(f" {header:-^80} ")
            logs.append("<br/>")
            if ansi_support():
                converter = ansi_support().Ansi2HTMLConverter(
                    inline=False, escaped=False
                )
                content = converter.convert(content, full=False)
            else:
                content = _remove_ansi_escape_sequences(content)
            logs.append(content.rstrip())
            logs.append("<br/>")
        return logs

    def append_log_html(
        self,
        report,
        additional_html,
        pytest_capture_value,
        pytest_show_capture_value,
    ):
        should_skip_captured_output = pytest_capture_value == "no"
        if report.outcome == "failed" and not should_skip_captured_output:
            should_skip_captured_output = pytest_show_capture_value == "no"
        if should_skip_captured_output:
            logs = []
        else:
            logs = self._populate_html_log_div(report)
        if logs:
            str_logs = "\n".join(logs)
            additional_html.append(f'<div class="log">{str_logs}</div>')
        else:
            additional_html.append(
                '<div class="empty log">No log output captured.</div>'
            )

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
            html_div = f'<a href="{content}">{base_extra_string.format(content)}</a>'
        elif self.self_contained:
            src = f"data:{extra.get('mime_type')};base64,{content}"
            html_div = base_extra_string.format(src)
        else:
            content = b64decode(content.encode("utf-8"))
            href = src = self.create_asset(
                content, extra_index, test_index, extra.get("extension"), "wb"
            )
            html_div = (
                f'<a class="{base_extra_class}" href="{href}" target="_blank">'
                f"{base_extra_string.format(src)}</a>"
            )
        return html_div

    def _append_image(self, extra, extra_index, test_index):
        image_base = '<img src="{}"/>'
        html_div = self._make_media_html_div(
            extra, extra_index, test_index, image_base, "image"
        )
        self.additional_html.append(f'<div class="image">{html_div}</div>')
        return None

    def _append_html(self, extra, extra_index, test_index):
        self.additional_html.append(f'<div>{extra.get("content")}</div>')
        return None

    def _append_json(self, extra, extra_index, test_index):
        content = json.dumps(extra.get("content"))
        if self.self_contained:
            return self._data_uri(content, mime_type=extra.get("mime_type"))
        else:
            return self.create_asset(
                content, extra_index, test_index, extra.get("extension")
            )

    def _append_text(self, extra, extra_index, test_index):
        content = extra.get("content")
        if isinstance(content, bytes):
            content = content.decode("utf-8")
        if self.self_contained:
            return self._data_uri(content)
        else:
            return self.create_asset(
                content, extra_index, test_index, extra.get("extension")
            )

    def _append_url(self, extra, extra_index, test_index):
        return extra.get("content")

    def _append_video(self, extra, extra_index, test_index):
        video_base = '<video controls><source src="{}" type="video/mp4"></video>'
        html_div = self._make_media_html_div(
            extra, extra_index, test_index, video_base, "video"
        )
        self.additional_html.append(f'<div class="video">{html_div}</div>')
        return None

    def _data_uri(self, content, mime_type="text/plain", charset="utf-8"):
        data = b64encode(content.encode(charset)).decode("ascii")
        return f"data:{mime_type};charset={charset};base64,{data}"

    def __str__(self):
        tmpl = self.jinja.get_template("result.html.jinja")
        return tmpl.render(
            outcome=self.outcome,
            columns=self.cells,
            additional_html="\n".join(self.additional_html),
            render_collapsed=self.render_collapsed,
        )
