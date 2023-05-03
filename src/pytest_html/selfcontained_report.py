# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import base64
import binascii
import warnings

from pytest_html.basereport import BaseReport


class SelfContainedReport(BaseReport):
    def __init__(self, report_path, config, report_data, template, css):
        super().__init__(report_path, config, report_data, template, css)

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
