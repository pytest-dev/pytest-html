pytest-html
===========

pytest-html is a plugin for `py.test <http://pytest.org>`_ that generates a
HTML report for the test results.

.. image:: https://img.shields.io/badge/license-MPL%202.0-blue.svg
   :target: https://github.com/davehunt/pytest-html/blob/master/LICENSE
   :alt: License
.. image:: https://img.shields.io/pypi/v/pytest-html.svg
   :target: https://pypi.python.org/pypi/pytest-html/
   :alt: PyPI
.. image:: https://img.shields.io/travis/davehunt/pytest-html.svg
   :target: https://travis-ci.org/davehunt/pytest-html/
   :alt: Travis
.. image:: https://img.shields.io/github/issues-raw/davehunt/pytest-html.svg
   :target: https://github.com/davehunt/pytest-html/issues
   :alt: Issues
.. image:: https://img.shields.io/requires/github/davehunt/pytest-html.svg
   :target: https://requires.io/github/davehunt/pytest-html/requirements/?branch=master
   :alt: Requirements

Requirements
------------

You will need the following prerequisites in order to use pytest-html:

- Python 2.6, 2.7, 3.2, 3.3, 3.4, PyPy, or PyPy3
- py.test 2.7 or newer

Installation
------------

To install pytest-html:

.. code-block:: bash

  $ pip install pytest-html

Then run your tests with:

.. code-block:: bash

  $ py.test --html=report.html

Enhancing reports
-----------------

You can add change the *Environment* section of the report by modifying
``request.config._html.environment`` from a fixture:

.. code-block:: python

  @pytest.fixture(autouse=True)
  def _environment(request):
      request.config._environment.append(('foo', 'bar'))

You can add details to the HTML reports by creating an 'extra' list on the
report object. The following example adds the various types of extras using a
:code:`pytest_runtest_makereport` hook, which can be implemented in a plugin or
conftest.py file:

.. code-block:: python

  from py.xml import html

  def pytest_runtest_makereport(__multicall__, item):
      pytest_html = item.config.pluginmanager.getplugin('html')
      report = __multicall__.execute()
      extra = getattr(report, 'extra', [])
      if report.when == 'call':
          # always add url to report
          extra.append(pytest_html.extras.url('http://www.example.com/'))
          xfail = hasattr(report, 'wasxfail')
          if (report.skipped and xfail) or (report.failed and not xfail):
              # only add additional html on failure
              extra.append(pytest_html.extras.html(html.div('Additional HTML')))
          report.extra = extra
      return report

Resources
---------

- `Issue Tracker <http://github.com/davehunt/pytest-html/issues>`_
- `Code <http://github.com/davehunt/pytest-html/>`_
