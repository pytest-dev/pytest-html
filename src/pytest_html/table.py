# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import re
import warnings


class Table:
    def __init__(self):
        self._html = {}

    @property
    def html(self):
        return self._html

    @html.setter
    def html(self, value):
        self._html = value


class Cell(Table):
    def __init__(self):
        super().__init__()
        self._append_counter = 0
        self._pop_counter = 0
        self._sortables = dict()

    def __setitem__(self, key, value):
        warnings.warn(
            "list-type assignment is deprecated and support "
            "will be removed in a future release. "
            "Please use 'insert()' instead.",
            DeprecationWarning,
        )
        self.insert(key, value)

    @property
    def sortables(self):
        return self._sortables

    def append(self, item):
        # We need a way of separating inserts from appends in JS,
        # hence the "Z" prefix
        self.insert(f"Z{self._append_counter}", item)
        self._append_counter += 1

    def insert(self, index, html):
        # backwards-compat
        if not isinstance(html, str):
            if html.__module__.startswith("py."):
                warnings.warn(
                    "The 'py' module is deprecated and support "
                    "will be removed in a future release.",
                    DeprecationWarning,
                )
            html = str(html)
            html = html.replace("col=", "data-column-type=")
        self._extract_sortable(html)
        self._html[index] = html

    def pop(self, *args):
        self._pop_counter += 1

    def get_pops(self):
        return self._pop_counter

    def _extract_sortable(self, html):
        match = re.search(r'<td class="col-(\w+)">(.*?)</', html)
        if match:
            sortable = match.group(1)
            value = match.group(2)
            self._sortables[sortable] = value


class Header(Cell):
    pass


class Row(Cell):
    def __delitem__(self, key):
        # This means the item should be removed
        self._html = None

    def pop(self, *args):
        # Calling pop on header is sufficient
        pass
