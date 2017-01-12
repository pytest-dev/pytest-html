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

- Python 2.6, 2.7, 3.3, 3.4, 3.5, PyPy, or PyPy3
- pytest 2.7 or newer

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
----------------------------------

In order to respect the `Content Security Policy (CSP)
<https://developer.mozilla.org/docs/Web/Security/CSP>`_,
several assets such as CSS and images are stored separately by default.
You can alternatively create a self-contained report, which can be more
convenient when sharing your results. This can be done in the following way:

.. code-block:: bash

   $ pytest --html=report.html --self-contained-html

Enhancing reports
-----------------

You can add change the *Environment* section of the report by modifying
``request.config._html.environment`` from a fixture:

.. code-block:: python

  @pytest.fixture(autouse=True)
  def _environment(request):
      request.config._environment.append(('foo', 'bar'))

You can add details to the HTML reports by creating an 'extra' list on the
report object. There are five different extras you can add:

- HTML: ``report.extra = [extra.html('<div>Additional HTML</div>')]``
- JSON: ``report.extra = [extra.json({'name': 'pytest'})]``
- TEXT: ``report.extra = [extra.text('Add some simple Text')]``
- URL:  ``report.extra = [extra.url('http://www.example.com/')]``

PNG, JPEG and SVG are predifend images types but you can add any image type you want.

- PNG: ``report.extra = [extra.png(image)]``
- JPG: ``report.extra = [extra.jpg(image)]``
- SVG: ``report.extra = [extra.svg(image)]``
- Any image type: ``report.extra = [extra.image(image, mime_type='image/gif', extension='gif')]``

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

Screenshots
-----------

.. image:: https://cloud.githubusercontent.com/assets/122800/11952194/62daa964-a88e-11e5-9745-2aa5b714c8bb.png
   :target: https://cloud.githubusercontent.com/assets/122800/11951695/f371b926-a88a-11e5-91c2-499166776bd3.png
   :alt: Enhanced HTML report

Resources
---------

- `Release Notes <http://github.com/pytest-dev/pytest-html/blob/master/CHANGES.rst>`_
- `Issue Tracker <http://github.com/pytest-dev/pytest-html/issues>`_
- `Code <http://github.com/pytest-dev/pytest-html/>`_
