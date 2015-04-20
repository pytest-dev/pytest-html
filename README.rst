pytest-html
===========

pytest-html is a plugin for `py.test <http://pytest.org>`_ that generates a
HTML report for the test results.

.. image:: https://travis-ci.org/davehunt/pytest-html.svg
    :target: https://travis-ci.org/davehunt/pytest-html

Requirements
------------

You will need the following prerequisites in order to use pytest-html:

- Python 2.6, 2.7 or PyPy
- py.test 2.3 or newer

Installation
------------

To install pytest-html::

    $ pip install pytest-html

Then run your tests with::

    $ py.test --html=report.html


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
          xfail = hasattr(report, 'wasxfail')
          if (report.skipped and xfail) or (report.failed and not xfail):
              url = TestSetup.selenium.current_url
              report.extra.append(extras.url(url))
              screenshot = TestSetup.selenium.get_screenshot_as_base64()
              report.extra.append(extras.image(screenshot, 'Screenshot'))
              html = TestSetup.selenium.page_source.encode('utf-8')
              report.extra.append(extra.text(html, 'HTML'))
              report.extra.append(extra.html(html.div('Additional HTML')))
          report.extra = extra
      return report

Resources
---------

- `Issue Tracker <http://github.com/davehunt/pytest-html/issues>`_
- `Code <http://github.com/davehunt/pytest-html/>`_
