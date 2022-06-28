import datetime
import json
import os
import re
import shutil

import pytest
from _pytest.pathlib import Path
from jinja2 import Environment
from jinja2 import FileSystemLoader

from . import __version__
from .util import cleanup_unserializable


class BaseReport(object):
    class Report(object):
        def __init__(self, title):
            self._data = {
                "title": title,
                "collectedItems": 0,
                "environment": {},
                "tests": [],
            }

        @property
        def data(self):
            return self._data

        @property
        def title(self):
            return self._data["title"]

        @title.setter
        def title(self, title):
            self._data["title"] = title

    def __init__(self, report_path, config):
        _plugin_path = os.path.dirname(__file__)
        self._report_path = Path(report_path).resolve()
        self._report_path.parent.mkdir(parents=True, exist_ok=True)

        self._resources_path = Path(_plugin_path, "resources")

        self._config = config
        self._css = None
        self._template = None
        self._template_filename = "index.jinja2"

        self._report = self.Report(self._report_path.name)

    def _generate_report(self, self_contained=False):
        generated = datetime.datetime.now()
        rendered_report = self._render_html(
            generated.strftime("%d-%b-%Y"),
            generated.strftime("%H:%M:%S"),
            __version__,
            self._css,
            self_contained=self_contained,
            test_data=cleanup_unserializable(self._report.data),
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

    def _read_template(self, search_paths):
        env = Environment(
            loader=FileSystemLoader(search_paths),
            autoescape=True,
        )

        return env.get_template(self._template_filename)

    def _render_html(
        self,
        date,
        time,
        version,
        styles,
        self_contained,
        test_data,
    ):
        return self._template.render(
            date=date,
            time=time,
            version=version,
            styles=styles,
            self_contained=self_contained,
            test_data=json.dumps(test_data),
        )

    def _write_report(self, rendered_report):
        with self._report_path.open("w", encoding="utf-8") as f:
            f.write(rendered_report)

    @pytest.hookimpl(trylast=True)
    def pytest_sessionstart(self, session):
        config = session.config
        if hasattr(config, "_metadata") and config._metadata:
            self._report.data["environment"] = self._generate_environment()

        self._generate_report()
        session.config.hook.pytest_html_report_title(report=self._report)

    @pytest.hookimpl(trylast=True)
    def pytest_collection_finish(self, session):
        self._report.data["collectedItems"] = len(session.items)

    @pytest.hookimpl(trylast=True)
    def pytest_runtest_logreport(self, report):
        data = self._config.hook.pytest_report_to_serializable(
            config=self._config, report=report
        )

        # # TODO rename to "extras" since list
        # if hasattr(report, "extra"):
        #     for extra in report.extra:
        #         if extra["mime_type"] is not None and "image" in extra["mime_type"]:
        #             data.update({"extras": extra})

        self._report.data["tests"].append(data)
        self._generate_report()


class NextGenReport(BaseReport):
    def __init__(self, report_path, config):
        super().__init__(report_path, config)
        self._assets_path = Path(self._report_path.parent, "assets")
        self._assets_path.mkdir(parents=True, exist_ok=True)
        self._default_css_path = Path(self._resources_path, "style.css")

        self._template = self._read_template(
            [self._resources_path, self._assets_path]
        )

        # Copy default css file (style.css) to assets directory
        new_css_path = shutil.copy(self._default_css_path, self._assets_path)
        self._css = [new_css_path] + self._config.getoption("css")


class NextGenSelfContainedReport(BaseReport):
    def __init__(self, report_path, config):
        super().__init__(report_path, config)
        self._template = self._read_template(
            [self._resources_path]
        )

        self._css = ["style.css"] + self._config.getoption("css")

    def _generate_report(self, *args, **kwargs):
        super()._generate_report(self_contained=True)
