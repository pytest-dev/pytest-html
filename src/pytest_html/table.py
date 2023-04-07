import re
import warnings


class Table:
    def __init__(self):
        self._html = {}

    @property
    def html(self):
        return self._html


class Html(Table):
    def __init__(self):
        super().__init__()
        self.html.setdefault("html", [])
        self._replace_log = False

    def __delitem__(self, key):
        # This means the log should be removed
        self._replace_log = True

    @property
    def replace_log(self):
        return self._replace_log

    def append(self, html):
        self.html["html"].append(html)


class Cell(Table):
    def __init__(self):
        super().__init__()
        self._append_counter = 0
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
        warnings.warn(
            "'pop' is deprecated and no longer supported.",
            DeprecationWarning,
        )

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
