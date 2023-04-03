import base64
import binascii
from pathlib import Path

from pytest_html.basereport import BaseReport


class Report(BaseReport):
    def __init__(self, report_path, config):
        super().__init__(report_path, config)
        self._assets_path = Path(self._report_path.parent, "assets")
        self._assets_path.mkdir(parents=True, exist_ok=True)
        self._css_path = Path(self._assets_path, "style.css")

        with self._css_path.open("w", encoding="utf-8") as f:
            f.write(self._css)

    @property
    def css(self):
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
