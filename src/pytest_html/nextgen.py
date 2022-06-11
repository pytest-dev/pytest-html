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
from .util import get_scripts


class BaseReport:
    def __init__(self, report_path, config):
        _plugin_path = os.path.dirname(__file__)
        self._report_absolute_path = Path(report_path).absolute()
        self._report_path = self._report_absolute_path.parent
        self._report_path.mkdir(parents=True, exist_ok=True)
        self._scripts_src_path = Path(_plugin_path, "scripts")
        self._resources_path = Path(_plugin_path, "resources")
        self._config = config
        self._template = None
        self._template_filename = "index.jinja2"

        self._data = {
            "title": "Test Report",
            "collectedItems": 0,
            "environment": {},
            "tests": [],
        }

    def _generate_report(self):
        pass

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
        scripts,
        self_contained,
        data_file=None,
        test_data=None,
    ):
        return self._template.render(
            date=date,
            time=time,
            version=version,
            styles=styles,
            scripts=scripts,
            self_contained=self_contained,
            data_file=data_file,
            test_data=test_data,
        )

    def _write_report(self, rendered_report):
        with self._report_absolute_path.open("w", encoding="utf-8") as f:
            f.write(rendered_report)

    @pytest.hookimpl(trylast=True)
    def pytest_sessionstart(self, session):
        config = session.config
        if hasattr(config, "_metadata") and config._metadata:
            self._data["environment"] = self._generate_environment()

        self._generate_report()

    @pytest.hookimpl(trylast=True)
    def pytest_collection_finish(self, session):
        self._data["collectedItems"] = len(session.items)

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

        self._data["tests"].append(data)
        self._generate_report()


class NextGenReport(BaseReport):
    def __init__(self, report_path, config):
        super().__init__(report_path, config)
        self._assets_path = Path(self._report_path, "assets")
        self._assets_path.mkdir(parents=True, exist_ok=True)
        self._scripts_dest_path = Path(self._report_path, "scripts")
        self._scripts_dest_path.mkdir(parents=True, exist_ok=True)
        self._default_css_path = Path(self._resources_path, "style.css")

    def _generate_report(self):
        self._template = self._read_template(
            [self._scripts_src_path, self._resources_path, self._assets_path]
        )

        # Copy scripts
        scripts_dest = shutil.copytree(
            self._scripts_src_path, self._scripts_dest_path, dirs_exist_ok=True
        )

        # Copy default css file (style.css) to assets directory
        new_css_path = shutil.copy(self._default_css_path, self._assets_path)

        generated = datetime.datetime.now()
        css_files = [new_css_path] + self._config.getoption("css")
        rendered_report = self._render_html(
            generated.strftime("%d-%b-%Y"),
            generated.strftime("%H:%M:%S"),
            __version__,
            css_files,
            get_scripts(scripts_dest),
            self_contained=False,
        )

        self._write_report(rendered_report)


class NextGenSelfContainedReport(BaseReport):
    def __init__(self, report_path, config):
        super().__init__(report_path, config)

    def _generate_report(self):
        self._template = self._read_template(
            [self._scripts_src_path, self._resources_path]
        )

        generated = datetime.datetime.now()
        css_files = ["style.css"] + self._config.getoption("css")
        rendered_report = self._render_html(
            generated.strftime("%d-%b-%Y"),
            generated.strftime("%H:%M:%S"),
            __version__,
            css_files,
            get_scripts(self._scripts_src_path),
            self_contained=True,
            test_data=cleanup_unserializable(self._data),
        )

        self._write_report(rendered_report)
