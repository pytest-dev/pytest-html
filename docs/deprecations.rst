Deprecations
============

Deprecation policy
------------------

If not otherwise explicitly stated, deprecations are removed in the next major version.

Deprecations
------------

duration_formatter
~~~~~~~~~~~~~~~~~~

Deprecated in ``4.0.0``

*'duration_formatter' has been removed and no longer has any effect!*

Reason
^^^^^^

With the rewrite of the plugin where most of the logic was moved to javascript,
the disconnect between time formatting between python and javascript made it
untenable to support dynamically setting the format.

The decision was made to have ``ms`` for durations under 1 second,
and ``HH:mm:ss`` for 1 second and above.

Mitigation
^^^^^^^^^^

Currently none.

render_collapsed
~~~~~~~~~~~~~~~~

Deprecated in ``4.0.0``

*'render_collapsed = True' is deprecated and support will be removed in the next major release.
Please use 'render_collapsed = all' instead.*

Reason
^^^^^^

We've changed the ini-config to better match the query param, so now the ini-config takes the same
values as the query param. For valid values please see :ref:`render-collapsed`.

Mitigation
^^^^^^^^^^

Setting ``render_collapsed`` to ``all`` is equivalent to previously setting it to ``True``.

.. _report-extra:

report.extra
~~~~~~~~~~~~

Deprecated in ``4.0.0``

*The 'report.extra' attribute is deprecated and will be removed in a future release,
use 'report.extras' instead.*

Reason
^^^^^^

The ``extra`` attribute is of type ``list``, hence more appropriately named ``extras``.

Mitigation
^^^^^^^^^^

Rename ``extra`` to ``extras``.

extra fixture
~~~~~~~~~~~~~

Deprecated in ``4.0.0``

*The 'extra' fixture is deprecated and will be removed in a future release,
use 'extras' instead.*

Reason
^^^^^^

See :ref:`report-extra`

Mitigation
^^^^^^^^^^

Rename ``extra`` to ``extras``.

cell list assignment
~~~~~~~~~~~~~~~~~~~~

Deprecated in ``4.0.0``

*list-type assignment is deprecated and support will be removed in a future release.
Please use 'insert()' instead.*

Reason
^^^^^^

The `cells` argument in the table manipulation hooks (see :ref:`modifying-results-table`) was
previously of type `list` but is now an object.

Mitigation
^^^^^^^^^^

Replace ``cells[4] = value`` with ``cells.insert(4, value)``.

py module
~~~~~~~~~

Deprecated in ``4.0.0``

*The 'py' module is deprecated and support will be removed in a future release.*

Reason
^^^^^^

The ``py`` module is in maintenance mode and has been removed as a dependency.

Mitigation
^^^^^^^^^^

Any usage of the ``html`` module from ``py.xml``, should be replaced with something
that returns the HTML as a string.

From:

.. code-block:: python

  import pytest
  from py.xml import html


  def pytest_html_results_table_header(cells):
      cells.insert(2, html.th("Description"))
      cells.insert(1, html.th("Time", class_="sortable time", data_column_type="time"))

To:

.. code-block:: python

  import pytest


  def pytest_html_results_table_header(cells):
      cells.insert(2, "<th>Description</th>")
      cells.insert(1, '<th class="sortable time" data-column-type="time">Time</th>')

Note that you can keep using the `py` module by simple wrapping it in ``str``:

.. code-block:: python

  import pytest
  from py.xml import html


  def pytest_html_results_table_header(cells):
      cells.insert(2, str(html.th("Description")))
      cells.insert(
          1, str(html.th("Time", class_="sortable time", data_column_type="time"))
      )
