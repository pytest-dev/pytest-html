import datetime
import json
import os

import pytest
import re
import shutil

from . import __version__
from .util import cleanup_unserializable, get_scripts

from jinja2 import Environment, FileSystemLoader, PackageLoader

from _pytest.pathlib import Path


class NextGenReport:
    def __init__(self, report_path, config):
        _plugin_path = os.path.dirname(__file__)
        self._report_absolute_path = Path(report_path).absolute()
        self._report_path = self._report_absolute_path.parent

        self._assets_path = Path(self._report_path, "assets")
        self._assets_path.mkdir(parents=True, exist_ok=True)

        self._scripts_dest_path = Path(self._report_path, "scripts")
        self._scripts_dest_path.mkdir(parents=True, exist_ok=True)
        self._scripts_src_path = Path(_plugin_path, "scripts")

        self._resources_path = Path(_plugin_path, "resources")

        self._default_css_path = Path(self._resources_path, "style.css")

        self._config = config
        self._data_file = Path(self._assets_path, "test_data.js")
        self._template = None
        self._template_filename = "index.jinja2"

        self._data = {
            "collectedItems": 0,
            "environment": {},
            "tests": [],
        }

    def _generate_environment(self):
        metadata = self._config._metadata
        for key in metadata.keys():
            value = metadata[key]
            if self._is_redactable_environment_variable(key):
                black_box_ascii_value = 0x2593
                metadata[key] = "".join(chr(black_box_ascii_value) for _ in str(value))

        return metadata

    def _generate_report(self):
        self._template = self._read_template()

        # Copy scripts
        scripts_dest = shutil.copytree(
            self._scripts_src_path, self._scripts_dest_path, dirs_exist_ok=True
        )

        # Copy default css file (style.css) to assets directory
        new_css_path = shutil.copy(self._default_css_path, self._assets_path)

        generated = datetime.datetime.now()
        css_files = [new_css_path] + self._config.getoption("css")
        rendered_report = self._render_html(
            "Test Report",
            generated.strftime("%d-%b-%Y"),
            generated.strftime("%H:%M:%S"),
            __version__,
            self._data_file.name,
            css_files,
            get_scripts(scripts_dest),
        )

        with self._report_absolute_path.open("w", encoding="utf-8") as f:
            f.write(rendered_report)

    def _is_redactable_environment_variable(self, environment_variable):
        redactable_regexes = self._config.getini("environment_table_redact_list")
        for redactable_regex in redactable_regexes:
            if re.match(redactable_regex, environment_variable):
                return True

        return False

    def _read_template(self):
        env = Environment(
            loader=FileSystemLoader(self._resources_path), autoescape=True
        )

        return env.get_template(self._template_filename)

    def _render_html(self, title, date, time, version, data_file, styles, scripts):
        return self._template.render(
            title=title,
            date=date,
            time=time,
            version=version,
            data_file=data_file,
            styles=styles,
            scripts=scripts,
        )

    def _write(self):
        try:
            data = json.dumps(self._data)
        except TypeError:
            data = cleanup_unserializable(self._data)
            data = json.dumps(data)

        with self._data_file.open("w", buffering=1, encoding="UTF-8") as f:
            f.write(f"const jsonData = {data}\n")

    @pytest.hookimpl(trylast=True)
    def pytest_sessionstart(self, session):
        config = session.config
        if hasattr(config, "_metadata") and config._metadata:
            self._data["environment"] = self._generate_environment()
            self._write()

        self._generate_report()

    @pytest.hookimpl(trylast=True)
    def pytest_collection_finish(self, session):
        self._data["collectedItems"] = len(session.items)
        self._write()

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
        self._write()
