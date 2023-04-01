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
            html = html.replace("col", "data-column-type")
        self._html[index] = html

    def pop(self, *args):
        warnings.warn(
            "'pop' is deprecated and no longer supported.",
            DeprecationWarning,
        )


class Header(Cell):
    pass


class Row(Cell):
    def __delitem__(self, key):
        # This means the item should be removed
        self._html = None
