pytest-html
===========

pytest-html is a plugin for `py.test <http://pytest.org>`_ that generates a
HTML report for the test results.

.. image:: https://img.shields.io/pypi/l/pytest-html.svg
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

- Python 2.6, 2.7, 3.2, 3.3, 3.4 or PyPy
- py.test 2.3 or newer

Installation
------------

To install pytest-html::

  pip install pytest-html

Then run your tests with::

  py.test --html=report.html


Enhancing reports
-----------------

You can add an *Environment* section to the report by implementing the
:code:`pytest_html_environment` hook and returning a dict representing the test
environment. For example:

.. code-block:: python

  def pytest_html_environment(config):
      return {'foo': 'bar'}

You can add details to the HTML reports by creating an 'extra' list on the
report object. The following example adds the various types of extras using a
:code:`pytest_runtest_makereport` hook, which can be implemented in a plugin or
conftest.py file:

.. code-block:: python

  from py.xml import html
  from html import extras

  def pytest_runtest_makereport(__multicall__, item):
      report = __multicall__.execute()
      extra = getattr(report, 'extra', [])
      if report.when == 'call':
          # always add url to report
          extra.append(extras.url('http://www.example.com/'))
          xfail = hasattr(report, 'wasxfail')
          if (report.skipped and xfail) or (report.failed and not xfail):
              # only add additional html on failure
              extra.append(extra.html(html.div('Additional HTML')))
          report.extra = extra
      return report

Resources
---------

- `Issue Tracker <http://github.com/davehunt/pytest-html/issues>`_
- `Code <http://github.com/davehunt/pytest-html/>`_
