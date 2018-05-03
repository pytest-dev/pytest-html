pytest-html
===========

pytest-html is a plugin for `pytest <http://pytest.org>`_ that generates a
HTML report for the test results.

.. image:: https://img.shields.io/badge/license-MPL%202.0-blue.svg
   :target: https://github.com/pytest-dev/pytest-html/blob/master/LICENSE
   :alt: License
.. image:: https://img.shields.io/pypi/v/pytest-html.svg
   :target: https://pypi.python.org/pypi/pytest-html/
   :alt: PyPI
.. image:: https://img.shields.io/travis/pytest-dev/pytest-html.svg
   :target: https://travis-ci.org/pytest-dev/pytest-html/
   :alt: Travis
.. image:: https://img.shields.io/github/issues-raw/pytest-dev/pytest-html.svg
   :target: https://github.com/pytest-dev/pytest-html/issues
   :alt: Issues
.. image:: https://img.shields.io/requires/github/pytest-dev/pytest-html.svg
   :target: https://requires.io/github/pytest-dev/pytest-html/requirements/?branch=master
   :alt: Requirements

Requirements
------------

You will need the following prerequisites in order to use pytest-html:

- Python 2.7, 3.6, PyPy, or PyPy3

Installation
------------

To install pytest-html:

.. code-block:: bash

  $ pip install pytest-html

Then run your tests with:

.. code-block:: bash

  $ pytest --html=report.html

ANSI codes
----------

Note that ANSI code support depends on the
`ansi2html <https://pypi.python.org/pypi/ansi2html/>`_ package. Due to the use
of a less permissive license, this package is not included as a dependency. If
you have this package installed, then ANSI codes will be converted to HTML in
your report.

Creating a self-contained report
--------------------------------

In order to respect the `Content Security Policy (CSP)
<https://developer.mozilla.org/docs/Web/Security/CSP>`_,
several assets such as CSS and images are stored separately by default.
You can alternatively create a self-contained report, which can be more
convenient when sharing your results. This can be done in the following way:

.. code-block:: bash

   $ pytest --html=report.html --self-contained-html

Images added as files or links are going to be linked as external resources,
meaning that the standalone report HTML-file may not display these images
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

Environment
~~~~~~~~~~~

The *Environment* section is provided by the `pytest-metadata
<https://pypi.python.org/pypi/pytest-metadata/>`_, plugin, and can be accessed
via the :code:`pytest_configure` hook:

.. code-block:: python

  def pytest_configure(config):
      config._metadata['foo'] = 'bar'

The generated table will be sorted alphabetically unless the metadata is a
:code:`collections.OrderedDict`.

Additional summary information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can edit the *Summary* section by using the :code:`pytest_html_results_summary` hook:

.. code-block:: python

   import pytest
   from py.xml import html

   @pytest.mark.optionalhook
   def pytest_html_results_summary(prefix, summary, postfix):
       prefix.extend([html.p("foo: bar")])

Extra content
~~~~~~~~~~~~~

You can add details to the HTML reports by creating an 'extra' list on the
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
  @pytest.mark.hookwrapper
  def pytest_runtest_makereport(item, call):
      pytest_html = item.config.pluginmanager.getplugin('html')
      outcome = yield
      report = outcome.get_result()
      extra = getattr(report, 'extra', [])
      if report.when == 'call':
          # always add url to report
          extra.append(pytest_html.extras.url('http://www.example.com/'))
          xfail = hasattr(report, 'wasxfail')
          if (report.skipped and xfail) or (report.failed and not xfail):
              # only add additional html on failure
              extra.append(pytest_html.extras.html('<div>Additional HTML</div>'))
          report.extra = extra

You can also specify the :code:`name` argument for all types other than :code:`html` which will change the title of the
created hyper link:

.. code-block:: python

    extra.append(pytest_html.extras.text('some string', name='Different title'))


Modifying the results table
~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can modify the columns by implementing custom hooks for the header and
rows. The following example :code:`conftest.py` adds a description column with
the test function docstring, adds a sortable time column, and removes the links
column:

.. code-block:: python

  from datetime import datetime
  from py.xml import html
  import pytest

  @pytest.mark.optionalhook
  def pytest_html_results_table_header(cells):
      cells.insert(2, html.th('Description'))
      cells.insert(1, html.th('Time', class_='sortable time', col='time'))
      cells.pop()

  @pytest.mark.optionalhook
  def pytest_html_results_table_row(report, cells):
      cells.insert(2, html.td(report.description))
      cells.insert(1, html.td(datetime.utcnow(), class_='col-time'))
      cells.pop()

  @pytest.mark.hookwrapper
  def pytest_runtest_makereport(item, call):
      outcome = yield
      report = outcome.get_result()
      report.description = str(item.function.__doc__)

You can also remove results by implementing the
:code:`pytest_html_results_table_row` hook and removing all cells. The
following example removes all passed results from the report:

.. code-block:: python

  import pytest

  @pytest.mark.optionalhook
  def pytest_html_results_table_row(report, cells):
      if report.passed:
        del cells[:]

The log output and additional HTML can be modified by implementing the
:code:`pytest_html_results_html` hook. The following example replaces all
additional HTML and log output with a notice that the log is empty:

.. code-block:: python

  import pytest

  @pytest.mark.optionalhook
  def pytest_html_results_table_html(report, data):
      if report.passed:
          del data[:]
          data.append(html.div('No log output captured.', class_='empty log'))

Screenshots
-----------

.. image:: https://cloud.githubusercontent.com/assets/122800/11952194/62daa964-a88e-11e5-9745-2aa5b714c8bb.png
   :target: https://cloud.githubusercontent.com/assets/122800/11951695/f371b926-a88a-11e5-91c2-499166776bd3.png
   :alt: Enhanced HTML report

Contributing
------------

Fork the repository and submit PRs with bug fixes and enhancements,  contributions are very welcome.

Tests can be run locally with `tox`_, for example to execute tests for Python 2.7 and 3.6 execute::

    tox -e py27,py36


.. _`tox`: https://tox.readthedocs.org/en/latest/

Resources
---------

- `Release Notes <http://github.com/pytest-dev/pytest-html/blob/master/CHANGES.rst>`_
- `Issue Tracker <http://github.com/pytest-dev/pytest-html/issues>`_
- `Code <http://github.com/pytest-dev/pytest-html/>`_

.. _JSON: http://json.org/
