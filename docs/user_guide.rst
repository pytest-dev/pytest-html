User Guide
==========

ANSI codes
----------

Note that ANSI code support depends on the `ansi2html`_ package. Due to the use
of a less permissive license, this package is not included as a dependency. If
you have this package installed, then ANSI codes will be converted to HTML in
your report.

Creating a self-contained report
--------------------------------

In order to respect the `Content Security Policy (CSP)`_, several assets such as
CSS and images are stored separately by default. You can alternatively create a
self-contained report, which can be more convenient when sharing your results.
This can be done in the following way:

.. code-block:: bash

   $ pytest --html=report.html --self-contained-html

Images added as files or links are going to be linked as external resources,
meaning that the standalone report HTML file may not display these images
as expected.

The plugin will issue a warning when adding files or links to the standalone report.

Enhancing reports
-----------------

Appearance
~~~~~~~~~~

Custom CSS (Cascasding Style Sheets) can be passed on the command line using
the :code:`--css` option. These will be applied in the order specified, and can
be used to change the appearance of the report.

.. code-block:: bash

  $ pytest --html=report.html --css=highcontrast.css --css=accessible.css

Report Title
~~~~~~~~~~~~

By default the report title will be the filename of the report, you can edit it by using the :code:`pytest_html_report_title` hook:

.. code-block:: python

   def pytest_html_report_title(report):
       report.title = "My very own title!"

Environment
~~~~~~~~~~~

The *Environment* section is provided by the `pytest-metadata`_ plugin, and can be accessed
via the :code:`pytest_configure` and :code:`pytest_sessionfinish` hooks:

To modify the *Environment* section **before** tests are run, use :code:`pytest_configure`:

.. code-block:: python

  from pytest_metadata.plugin import metadata_key


  def pytest_configure(config):
      config.stash[metadata_key]["foo"] = "bar"

To modify the *Environment* section **after** tests are run, use :code:`pytest_sessionfinish`:

.. code-block:: python

  import pytest
  from pytest_metadata.plugin import metadata_key


  @pytest.hookimpl(tryfirst=True)
  def pytest_sessionfinish(session, exitstatus):
      session.config.stash[metadata_key]["foo"] = "bar"

Note that in the above example `@pytest.hookimpl(tryfirst=True)`_ is important, as this ensures that a best effort attempt is made to run your
:code:`pytest_sessionfinish` **before** any other plugins ( including :code:`pytest-html` and :code:`pytest-metadata` ) run theirs.
If this line is omitted, then the *Environment* table will **not** be updated since the :code:`pytest_sessionfinish` of the plugins will execute first,
and thus not pick up your change.

The generated table will be sorted alphabetically unless the metadata is a :code:`collections.OrderedDict`.

It is possible to redact variables from the environment table. Redacted variables will have their names displayed, but their values grayed out.
This can be achieved by setting :code:`environment_table_redact_list` in your INI configuration file (e.g.: :code:`pytest.ini`).
:code:`environment_table_redact_list` is a :code:`linelist` of regexes. Any environment table variable that matches a regex in this list has its value redacted.

For example, the following will redact all environment table variables that match the regexes :code:`^foo$`, :code:`.*redact.*`, or :code:`bar`:

.. code-block:: ini

  [pytest]
  environment_table_redact_list = ^foo$
      .*redact.*
      bar

Additional summary information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can edit the *Summary* section by using the :code:`pytest_html_results_summary` hook:

.. code-block:: python

   def pytest_html_results_summary(prefix, summary, postfix):
       prefix.extend(["<p>foo: bar</p>"])

Extra content
~~~~~~~~~~~~~

You can add details to the HTML report by creating an 'extras' list on the
report object. Here are the types of extra content that can be added:

==========  ============================================
Type        Example
==========  ============================================
Raw HTML    ``extras.html('<div>Additional HTML</div>')``
`JSON`_     ``extras.json({'name': 'pytest'})``
Plain text  ``extras.text('Add some simple Text')``
URL         ``extras.url('http://www.example.com/')``
Image       ``extras.image(image, mime_type='image/gif', extension='gif')``
Image       ``extras.image('/path/to/file.png')``
Image       ``extras.image('http://some_image.png')``
==========  ============================================

**Note**: When adding an image from file, the path can be either absolute
or relative.

**Note**: When using ``--self-contained-html``, images added as files or links
may not work as expected, see section `Creating a self-contained report`_ for
more info.

There are also convenient types for several image formats:

============  ====================
Image format  Example
============  ====================
PNG           ``extras.png(image)``
JPEG          ``extras.jpg(image)``
SVG           ``extras.svg(image)``
============  ====================

The following example adds the various types of extras using a
:code:`pytest_runtest_makereport` hook, which can be implemented in a plugin or
conftest.py file:

.. code-block:: python

  import pytest
  import pytest_html


  @pytest.hookimpl(hookwrapper=True)
  def pytest_runtest_makereport(item, call):
      outcome = yield
      report = outcome.get_result()
      extras = getattr(report, "extras", [])
      if report.when == "call":
          # always add url to report
          extras.append(pytest_html.extras.url("http://www.example.com/"))
          xfail = hasattr(report, "wasxfail")
          if (report.skipped and xfail) or (report.failed and not xfail):
              # only add additional html on failure
              extras.append(pytest_html.extras.html("<div>Additional HTML</div>"))
          report.extras = extras

You can also specify the :code:`name` argument for all types other than :code:`html` which will change the title of the
created hyper link:

.. code-block:: python

    extras.append(pytest_html.extras.text("some string", name="Different title"))

It is also possible to use the fixture :code:`extras` to add content directly
in a test function without implementing hooks. These will generally end up
before any extras added by plugins.

.. code-block:: python

   import pytest_html


   def test_extra(extras):
       extras.append(pytest_html.extras.text("some string"))


.. _modifying-results-table:

Modifying the results table
~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can modify the columns of the report by implementing custom hooks for the header and rows.
The following example :code:`conftest.py` adds a description column with the test function docstring,
adds a sortable time column, and removes the links column:

.. code-block:: python

  import pytest


  def pytest_html_results_table_header(cells):
      cells.insert(2, "<th>Description</th>")
      cells.insert(1, '<th class="sortable time" data-column-type="time">Time</th>')


  def pytest_html_results_table_row(report, cells):
      cells.insert(2, "<td>A description</td>")
      cells.insert(1, '<td class="col-time">A time</td>')


  @pytest.hookimpl(hookwrapper=True)
  def pytest_runtest_makereport(item, call):
      outcome = yield
      report = outcome.get_result()
      report.description = str(item.function.__doc__)

You can also remove results by implementing the
:code:`pytest_html_results_table_row` hook and removing all cells. The
following example removes all passed results from the report:

.. code-block:: python

  def pytest_html_results_table_row(report, cells):
      if report.passed:
          del cells[:]

The log output and additional HTML can be modified by implementing the
:code:`pytest_html_results_html` hook. The following example replaces all
additional HTML and log output with a notice that the log is empty:

.. code-block:: python

  def pytest_html_results_table_html(report, data):
      if report.passed:
          del data[:]
          data.append("<div class='empty log'>No log output captured.</div>")

Display options
---------------

.. _render-collapsed:

Auto Collapsing Table Rows
~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, all rows in the **Results** table will be expanded except those that have :code:`Passed`.

This behavior can be customized with a query parameter: :code:`?collapsed=Passed,XFailed,Skipped`.
If you want all rows to be collapsed you can pass :code:`?collapsed=All`.
By setting the query parameter to empty string :code:`?collapsed=""` **none** of the rows will be collapsed.

Note that the query parameter is case insensitive, so passing :code:`PASSED` and :code:`passed` has the same effect.

You can also set the collapsed behaviour by setting :code:`render_collapsed` in a configuration file (pytest.ini, setup.cfg, etc).
Note that the query parameter takes precedence.

.. code-block:: ini

  [pytest]
  render_collapsed = failed,error

Controlling Test Result Visibility
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, all tests are visible, regardless of their results. It is possible to control which tests are visible on
page load by passing the :code:`visible` query parameter. To use this parameter, please pass a comma separated list
of test results you wish to be visible. For example, passing :code:`?visible=passed,skipped` will show only those
tests in the report that have outcome :code:`passed` or :code:`skipped`.

Note that this match is case insensitive, so passing :code:`PASSED` and :code:`passed` has the same effect.

The following values may be passed:

* :code:`passed`
* :code:`skipped`
* :code:`failed`
* :code:`error`
* :code:`xfailed`
* :code:`xpassed`
* :code:`rerun`

Results Table Sorting
~~~~~~~~~~~~~~~~~~~~~

You can change which column the results table is sorted on, on page load by passing the :code:`sort` query parameter.

You can also set the initial sorting by setting :code:`initial_sort` in a configuration file (pytest.ini, setup.cfg, etc).
Note that the query parameter takes precedence.

The following values may be passed:

* :code:`result`
* :code:`testId`
* :code:`duration`
* :code:`original`

Note that the values are case *sensitive*.

``original`` means that a best effort is made to sort the table in the order of execution.
If tests are run in parallel (with `pytest-xdist`_ for example), then the order may not be
in the correct order.


.. _@pytest.hookimpl(tryfirst=True): https://docs.pytest.org/en/stable/writing_plugins.html#hook-function-ordering-call-example
.. _ansi2html: https://pypi.python.org/pypi/ansi2html/
.. _Content Security Policy (CSP): https://developer.mozilla.org/docs/Web/Security/CSP/
.. _JSON: https://json.org/
.. _pytest-metadata: https://pypi.python.org/pypi/pytest-metadata/
.. _pytest-xdist: https://pypi.python.org/pypi/pytest-xdist/
.. _time.strftime: https://docs.python.org/3/library/time.html#time.strftime
