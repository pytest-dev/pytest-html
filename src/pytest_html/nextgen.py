import json
from typing import Any
from typing import Dict

import pytest


class NextGenReport:
    def __init__(self, config, data_file):
        self._config = config
        self._data_file = data_file

        self._title = "Next Gen Report"
        self._data = {
            "title": self._title,
            "collectedItems": 0,
            "environment": {},
            "tests": [],
        }

        self._data_file.parent.mkdir(parents=True, exist_ok=True)

    def _write(self):
        try:
            data = json.dumps(self._data)
        except TypeError:
            data = cleanup_unserializable(self._data)
            data = json.dumps(data)

        with self._data_file.open("w", buffering=1, encoding="UTF-8") as f:
            f.write("const jsonData = ")
            f.write(data)
            f.write("\n")

    @pytest.hookimpl(trylast=True)
    def pytest_sessionstart(self, session):
        config = session.config
        if hasattr(config, "_metadata") and config._metadata:
            metadata = config._metadata
            self._data["environment"] = metadata
            self._write()

    @pytest.hookimpl(trylast=True)
    def pytest_collection_finish(self, session):
        self._data["collectedItems"] = len(session.items)
        self._write()

    @pytest.hookimpl(trylast=True)
    def pytest_runtest_logreport(self, report):
        data = self._config.hook.pytest_report_to_serializable(
            config=self._config, report=report
        )
        self._data["tests"].append(data)
        self._write()


def cleanup_unserializable(d: Dict[str, Any]) -> Dict[str, Any]:
    """Return new dict with entries that are not json serializable by their str()."""
    result = {}
    for k, v in d.items():
        try:
            json.dumps({k: v})
        except TypeError:
            v = str(v)
        result[k] = v
    return result
