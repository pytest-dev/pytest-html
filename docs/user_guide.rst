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

  def pytest_configure(config):
      config._metadata["foo"] = "bar"

To modify the *Environment* section **after** tests are run, use :code:`pytest_sessionfinish`:

.. code-block:: python

  import pytest


  @pytest.hookimpl(tryfirst=True)
  def pytest_sessionfinish(session, exitstatus):
      session.config._metadata["foo"] = "bar"

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

   from py.xml import html


   def pytest_html_results_summary(prefix, summary, postfix):
       prefix.extend([html.p("foo: bar")])

Extra content
~~~~~~~~~~~~~

You can add details to the HTML report by creating an 'extra' list on the
report object. Here are the types of extra content that can be added:

==========  ============================================
Type        Example
==========  ============================================
Raw HTML    ``extra.html('<div>Additional HTML</div>')``
`JSON`_     ``extra.json({'name': 'pytest'})``
Plain text  ``extra.text('Add some simple Text')``
URL         ``extra.url('http://www.example.com/')``
Image       ``extra.image(image, mime_type='image/gif', extension='gif')``
Image       ``extra.image('/path/to/file.png')``
Image       ``extra.image('http://some_image.png')``
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
PNG           ``extra.png(image)``
JPEG          ``extra.jpg(image)``
SVG           ``extra.svg(image)``
============  ====================

The following example adds the various types of extras using a
:code:`pytest_runtest_makereport` hook, which can be implemented in a plugin or
conftest.py file:

.. code-block:: python

  import pytest


  @pytest.hookimpl(hookwrapper=True)
  def pytest_runtest_makereport(item, call):
      pytest_html = item.config.pluginmanager.getplugin("html")
      outcome = yield
      report = outcome.get_result()
      extra = getattr(report, "extra", [])
      if report.when == "call":
          # always add url to report
          extra.append(pytest_html.extras.url("http://www.example.com/"))
          xfail = hasattr(report, "wasxfail")
          if (report.skipped and xfail) or (report.failed and not xfail):
              # only add additional html on failure
              extra.append(pytest_html.extras.html("<div>Additional HTML</div>"))
          report.extra = extra

You can also specify the :code:`name` argument for all types other than :code:`html` which will change the title of the
created hyper link:

.. code-block:: python

    extra.append(pytest_html.extras.text("some string", name="Different title"))

It is also possible to use the fixture :code:`extra` to add content directly
in a test function without implementing hooks. These will generally end up
before any extras added by plugins.

.. code-block:: python

   from pytest_html import extras


   def test_extra(extra):
       extra.append(extras.text("some string"))


Modifying the results table
~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can modify the columns of the report by implementing custom hooks for the header and rows.
The following example :code:`conftest.py` adds a description column with the test function docstring,
adds a sortable time column, and removes the links column:

.. code-block:: python

  from datetime import datetime
  from py.xml import html
  import pytest


  def pytest_html_results_table_header(cells):
      cells.insert(2, html.th("Description"))
      cells.insert(1, html.th("Time", class_="sortable time", col="time"))
      cells.pop()


  def pytest_html_results_table_row(report, cells):
      cells.insert(2, html.td(report.description))
      cells.insert(1, html.td(datetime.utcnow(), class_="col-time"))
      cells.pop()


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

  from py.xml import html


  def pytest_html_results_table_html(report, data):
      if report.passed:
          del data[:]
          data.append(html.div("No log output captured.", class_="empty log"))

Display options
---------------

Auto Collapsing Table Rows
~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, all rows in the **Results** table will be expanded except those that have :code:`Passed`.

This behavior can be customized either with a query parameter: :code:`?collapsed=Passed,XFailed,Skipped`
or by setting the :code:`render_collapsed` in a configuration file (pytest.ini, setup.cfg, etc).

.. code-block:: ini

  [pytest]
  render_collapsed = True

**NOTE:** Setting :code:`render_collapsed` will, unlike the query parameter, affect all statuses.

Controlling Test Result Visibility Via Query Params
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, all tests are visible, regardless of their results. It is possible to control which tests are visible on
page load by passing the :code:`visible` query parameter. To use this parameter, please pass a comma separated list
of test results you wish to be visible. For example, passing :code:`?visible=passed,skipped` will show only those
tests in the report that have outcome :code:`passed` or :code:`skipped`.

Note that this match is case insensitive, so passing :code:`PASSED` and :code:`passed` has the same effect.

The following query parameters may be passed:

* :code:`passed`
* :code:`skipped`
* :code:`failed`
* :code:`error`
* :code:`xfailed`
* :code:`xpassed`
* :code:`rerun`

Formatting the Duration Column
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The formatting of the timestamp used in the :code:`Durations` column can be modified by setting :code:`duration_formatter`
on the :code:`report` attribute. All `time.strftime`_ formatting directives are supported. In addition, it is possible
to supply :code:`%f` to get duration milliseconds. If this value is not set, the values in the :code:`Durations` column are
displayed in :code:`%S.%f` format where :code:`%S` is the total number of seconds a test ran for.

Below is an example of a :code:`conftest.py` file setting :code:`duration_formatter`:

.. code-block:: python

   import pytest


   @pytest.hookimpl(hookwrapper=True)
   def pytest_runtest_makereport(item, call):
       outcome = yield
       report = outcome.get_result()
       setattr(report, "duration_formatter", "%H:%M:%S.%f")

**NOTE**: Milliseconds are always displayed with a precision of 2

.. _@pytest.hookimpl(tryfirst=True): https://docs.pytest.org/en/stable/writing_plugins.html#hook-function-ordering-call-example
.. _ansi2html: https://pypi.python.org/pypi/ansi2html/
.. _Content Security Policy (CSP): https://developer.mozilla.org/docs/Web/Security/CSP/
.. _JSON: https://json.org/
.. _pytest-metadata: https://pypi.python.org/pypi/pytest-metadata/
.. _time.strftime: https://docs.python.org/3/library/time.html#time.strftime
