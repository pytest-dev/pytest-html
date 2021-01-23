Changelog
=========

Versions follow `Semantic Versioning`_ (``<major>.<minor>.<patch>``).

Version History
---------------

3.2.0 (unreleased)
~~~~~~~~~~~~~~~~~~

* Implement the ``visible`` URL query parameter to control visibility of test results on page load. (`#399 <https://github.com/pytest-dev/pytest-html/issues/399>`_)

  * Thanks to `@TheCorp <https://github.com/TheCorp>`_ for reporting and `@gnikonorov <https://github.com/gnikonorov>`_ for the fix

* Make the report tab title reflect the report name. (`#412 <https://github.com/pytest-dev/pytest-html/issues/412>`_)

  * Thanks to `@gnikonorov <https://github.com/gnikonorov>`_ for the PR

* Implement :code:`environment_table_redact_list` to allow for redaction of environment table values. (`#233 <https://github.com/pytest-dev/pytest-html/issues/233>`_)

  * Thanks to `@fenchu <https://github.com/fenchu>`_ for reporting and `@gnikonorov <https://github.com/gnikonorov>`_ for the PR

3.1.1 (2020-12-13)
~~~~~~~~~~~~~~~~~~

* Fix issue with reporting of missing CSS files. (`#388 <https://github.com/pytest-dev/pytest-html/issues/388>`_)

  * Thanks to `@prakhargurunani <https://github.com/prakhargurunani>`_ for reporting and fixing!

3.1.0 (2020-12-2)
~~~~~~~~~~~~~~~~~

* Stop attaching test reruns to final test report entries (`#374 <https://github.com/pytest-dev/pytest-html/issues/374>`_)

  * Thanks to `@VladimirPodolyan <https://github.com/VladimirPodolyan>`_ for reporting and `@gnikonorov <https://github.com/gnikonorov>`_ for the fix

* Allow for report duration formatting (`#376 <https://github.com/pytest-dev/pytest-html/issues/376>`_)

  * Thanks to `@brettnolan <https://github.com/brettnolan>`_ for reporting and `@gnikonorov <https://github.com/gnikonorov>`_ for the fix

3.0.0 (2020-10-28)
~~~~~~~~~~~~~~~~~~

* Respect ``--capture=no``, ``--show-capture=no``, and ``-s`` pytest flags (`#171 <https://github.com/pytest-dev/pytest-html/issues/171>`_)

  * Thanks to `@bigunyak <https://github.com/bigunyak>`_ for reporting and `@gnikonorov <https://github.com/gnikonorov>`_ for the fix

* Make the ``Results`` table ``Links`` column sortable (`#242 <https://github.com/pytest-dev/pytest-html/issues/242>`_)

  * Thanks to `@vashirov <https://github.com/vashirov>`_ for reporting and `@gnikonorov <https://github.com/gnikonorov>`_ for the fix

* Fix issue with missing image or video in extras. (`#265 <https://github.com/pytest-dev/pytest-html/issues/265>`_ and `pytest-selenium#237 <https://github.com/pytest-dev/pytest-selenium/issues/237>`_)

  * Thanks to `@p00j4 <https://github.com/p00j4>`_ and `@anothermattbrown <https://github.com/anothermattbrown>`_ for reporting and `@christiansandberg <https://github.com/christiansandberg>`_ and `@superdodd <https://github.com/superdodd>`_ and `@dhalperi <https://github.com/dhalperi>`_ for the fix

* Fix attribute name for compatibility with ``pytest-xdist`` 2. (`#305 <https://github.com/pytest-dev/pytest-html/issues/305>`_)

  * Thanks to `@Zac-HD <https://github.com/Zac-HD>`_ for the fix

* Post process HTML generation to allow teardown to appear in the HTML output. (`#131 <https://github.com/pytest-dev/pytest-html/issues/131>`_)

  * Thanks to `@iwanb <https://github.com/iwanb>`_ for reporting and `@csm10495 <https://github.com/csm10495>`_ for the fix

2.1.1 (2020-03-18)
~~~~~~~~~~~~~~~~~~

* Fix issue with funcargs causing failures. (`#282 <https://github.com/pytest-dev/pytest-html/issues/282>`_)

  * Thanks to `@ssbarnea <https://github.com/ssbarnea>`_ for reporting and `@christiansandberg <https://github.com/christiansandberg>`_ for the fix

2.1.0 (2020-03-09)
~~~~~~~~~~~~~~~~~~

* Added support for MP4 video format. (`#260 <https://github.com/pytest-dev/pytest-html/pull/260>`_)

  * Thanks to `@ExaltedBagel <https://github.com/ExaltedBagel>`_ for the PR

* Added support for sorting metadata by key. (`#245 <https://github.com/pytest-dev/pytest-html/issues/245>`_)

  * Thanks to `@ssbarnea <https://github.com/ssbarnea>`_ for reporting and `@ExaltedBagel <https://github.com/ExaltedBagel>`_ for the fix

* Added support for rendering reports collapsed (`#239 <https://github.com/pytest-dev/pytest-html/issues/239>`_)

  * Thanks to `@Wramberg <https://github.com/Wramberg>`_ for suggesting this enhancement

* Added `extra` fixture (`#269 <https://github.com/pytest-dev/pytest-html/pull/269>`_)

  * Thanks to `@christiansandberg <https://github.com/christiansandberg>`_ for the PR

* Added ability to change report title using hook (`#270 <https://github.com/pytest-dev/pytest-html/pull/270>`_)

  * Thanks to `@werdeil <https://github.com/werdeil>`_ for the PR

2.0.1 (2019-10-05)
~~~~~~~~~~~~~~~~~~

* Properly check for presence of CSS file. (`#246 <https://github.com/pytest-dev/pytest-html/issues/246>`_)

  * Thanks to `@wanam <https://github.com/wanam>`_ for reporting, and `@krzysztof-pawlik-gat <https://github.com/krzysztof-pawlik-gat>`_ for the fix

* Added support for UTF-8 display. (`#244 <https://github.com/pytest-dev/pytest-html/pull/244>`_)

  * Thanks to `@Izhu666 <https://github.com/lzhu666>`_ for the PR

* Fix initial sort on column. (`#247 <https://github.com/pytest-dev/pytest-html/issues/247>`_)

  * Thanks to `@wanam <https://github.com/wanam>`_ for reporting and fixing

2.0.0 (2019-09-09)
~~~~~~~~~~~~~~~~~~

* Drop support for Python 2.7. We will continue to accept patches to ``1.22.x`` for the time being.

  * Thanks to `@hugovk <https://github.com/hugovk>`_ for the PR

1.22.0 (2019-08-06)
~~~~~~~~~~~~~~~~~~~

* Refactor assets naming to be more readable and OS safe.

  * This solves multiple reported issues, mainly from Windows users.
  * Thanks to `@franz-95 <https://github.com/franz-95>`_ and `@Uil2Liv <https://github.com/Uil2liv>`_
    for reporting and testing fixes.

* Add line break to log section of the report.

  * Thanks to `@borntyping <https://github.com/borntyping>`_ for reporting and fixing!

1.21.1 (2019-06-19)
~~~~~~~~~~~~~~~~~~~

* Fix issue with assets filenames being too long.

  * Thanks to `@D3X <https://github.com/D3X>`_ for reporting and providing a fix

1.21.0 (2019-06-17)
~~~~~~~~~~~~~~~~~~~

* Allow opening generated html report in browser (`@ssbarnea <https://github.com/ssbarnea>`_)

* Handle when report title is stored as an environment variable (`@BeyondEvil <https://github.com/BeyondEvil>`_)

* Change assets naming method (`@SunInJuly <https://github.com/SunInJuly>`_)

1.20.0 (2019-01-14)
~~~~~~~~~~~~~~~~~~~

* Tests running with Pytest 4.0 and Python 3.7

* Stop filtering out falsy environment values (`#175 <https://github.com/pytest-dev/pytest-html/issues/175>`_)

  * Thanks to `@jknotts <https://github.com/jknotts>`_ for reporting the issue
    and to `@crazymerlyn <http://github.com/crazymerlyn>`_ for providing a fix

* Removed extraneous space from anchor tag (`@chardbury <https://github.com/chardbury>`_)

* Always define __version__ even if get_distribution() fails (`@nicoddemus <https://github.com/nicoddemus>`_)

* Refactor css config code (`@crazymerlyn <http://github.com/crazymerlyn>`_)

1.19.0 (2018-06-01)
~~~~~~~~~~~~~~~~~~~

* Allow collapsed outcomes to be configured by using a query parameter

  * Thanks to `@Formartha <https://github.com/Formartha>`_ for suggesting this
    enhancement and to `@jacebrowning <https://github.com/jacebrowning>`_ for
    providing a patch

1.18.0 (2018-05-22)
~~~~~~~~~~~~~~~~~~~

* Preserve the order if metadata is ``OrderedDict``

  * Thanks to `@jacebrowning <https://github.com/jacebrowning>`_ for suggesting
    this enhancement and providing a patch

1.17.0 (2018-04-05)
~~~~~~~~~~~~~~~~~~~

* Add support for custom CSS (`#116 <https://github.com/pytest-dev/pytest-html/issues/116>`_)

  * Thanks to `@APshenkin <https://github.com/APshenkin>`_ for reporting the
    issue and to `@i-am-david-fernandez
    <https://github.com/i-am-david-fernandez>`_ for providing a fix

* Report collection errors (`#148 <https://github.com/pytest-dev/pytest-html/issues/148>`_)

  * Thanks to `@Formartha <https://github.com/Formartha>`_ for reporting the
    issue

* Add hook for modifying summary section (`#109 <https://github.com/pytest-dev/pytest-html/issues/109>`_)

  * Thanks to `@shreyashah <https://github.com/shreyashah>`_ for reporting the
    issue and to `@j19sch <https://github.com/j19sch>`_ for providing a
    fix

* Add filename to report as heading

  * Thanks to `@j19sch <https://github.com/j19sch>`_ for the PR


1.16.1 (2018-01-04)
~~~~~~~~~~~~~~~~~~~

* Fix for including screenshots on Windows
  (`#124 <https://github.com/pytest-dev/pytest-html/issues/124>`_)

  * Thanks to `@ngavrish <https://github.com/ngavrish>`_ for reporting the
    issue and to `@pinkie1378 <https://github.com/pinkie1378>`_ for providing a
    fix

1.16.0 (2017-09-19)
~~~~~~~~~~~~~~~~~~~

* Improve rendering of collections in metadata
  (`@rasmuspeders1 <https://github.com/rasmuspeders1>`_)

1.15.2 (2017-08-15)
~~~~~~~~~~~~~~~~~~~

* Always decode byte string in extra text

  * Thanks to `@ch-t <https://github.com/ch-t>`_ for reporting the issue and
    providing a fix

1.15.1 (2017-06-12)
~~~~~~~~~~~~~~~~~~~

* Fix pytest dependency to 3.0 or later

  * Thanks to `@silvana-i <https://github.com/silvana-i>`_ for reporting the
    issue and to `@nicoddemus <https://github.com/nicoddemus>`_ for providing a
    fix

1.15.0 (2017-06-09)
~~~~~~~~~~~~~~~~~~~

* Fix encoding issue in longrepr values

  * Thanks to `@tomga <https://github.com/tomga>`_ for reporting the issue and
    providing a fix

* Add ability to specify images as file or URL

  * Thanks to `@BeyondEvil <https://github.com/BeyondEvil>`_ for the PR

1.14.2 (2017-03-10)
~~~~~~~~~~~~~~~~~~~

* Always encode content for data URI

  * Thanks to `@micheletest <https://github.com/micheletest>`_ and
    `@BeyondEvil <https://github.com/BeyondEvil>`_ for reporting the issue and
    confirming the fix

1.14.1 (2017-02-28)
~~~~~~~~~~~~~~~~~~~

* Present metadata without additional formatting to avoid issues due to
  unpredictable content types

1.14.0 (2017-02-27)
~~~~~~~~~~~~~~~~~~~

* Add hooks for modifying the test results table
* Replace environment section with values from
  `pytest-metadata <https://pypi.python.org/pypi/pytest-metadata/>`_
* Fix encoding for asset files
* Escape contents of log sections

1.13.0 (2016-12-19)
~~~~~~~~~~~~~~~~~~~

* Disable ANSI codes support by default due to dependency on
  `ansi2html <https://pypi.python.org/pypi/ansi2html/>`_ package with less
  permissive licensing

1.12.0 (2016-11-30)
~~~~~~~~~~~~~~~~~~~

* Add support for JPG and SVG images
  (`@bhzunami <https://github.com/bhzunami>`_)
* Add version number and PyPI link to report header
  (`@denisra <https://github.com/denisra>`_)

1.11.1 (2016-11-25)
~~~~~~~~~~~~~~~~~~~

* Fix title of checkbox disappearing when unchecked
  (`@vashirov <https://github.com/vashirov>`_)

1.11.0 (2016-11-08)
~~~~~~~~~~~~~~~~~~~

* Add support for ANSI codes in logs
  (`@premkarat <https://github.com/premkarat>`_)

1.10.1 (2016-09-23)
~~~~~~~~~~~~~~~~~~~

* Fix corrupt image asset files
* Remove image links from self-contained report
* Fix issue with unexpected passes not being reported in pytest 3.0

1.10.0 (2016-08-09)
~~~~~~~~~~~~~~~~~~~

* Hide filter checkboxes when JavaScript is disabled
  (`@RibeiroAna <https://github.com/RibeiroAna>`_)
* Removed rerun outcome unless the plugin is active
  (`@RibeiroAna <https://github.com/RibeiroAna>`_)
* Introduce ``--self-contained-html`` option to store CSS and assets inline
  (`@RibeiroAna <https://github.com/RibeiroAna>`_)
* Save images, text, and JSON extras as files in an assets directory
  (`@RibeiroAna <https://github.com/RibeiroAna>`_)
* Use an external CSS file
  (`@RibeiroAna <https://github.com/RibeiroAna>`_)
* Set initial sort order in the HTML
  (`@RibeiroAna <https://github.com/RibeiroAna>`_)
* Allow visibility of extra details to be toggled
  (`@leitzler <https://github.com/leitzler>`_)

1.9.0 (2016-07-04)
~~~~~~~~~~~~~~~~~~

* Split pytest_sessionfinish into generate and save methods
  (`@karandesai-96 <https://github.com/karandesai-96>`_)
* Show tests rerun by pytest-rerunfailures plugin
  (`@RibeiroAna <https://github.com/RibeiroAna>`_)
* Added a feature to filter tests by outcome
  (`@RibeiroAna <https://github.com/RibeiroAna>`_)

1.8.1 (2016-05-24)
~~~~~~~~~~~~~~~~~~

* Include captured output for passing tests

1.8.0 (2016-02-24)
~~~~~~~~~~~~~~~~~~

* Remove duplication from the environment section
* Dropped support for Python 3.2
* Indicated setup and teardown in report
* Fixed colour of errors in report

1.7 (2015-10-19)
~~~~~~~~~~~~~~~~

* Fixed INTERNALERROR when an xdist worker crashes
  (`@The-Compiler <https://github.com/The-Compiler>`_)
* Added report sections including stdout and stderr to log

1.6 (2015-09-08)
~~~~~~~~~~~~~~~~

* Fixed environment details when using pytest-xdist

1.5.1 (2015-08-18)
~~~~~~~~~~~~~~~~~~

* Made environment fixture session scoped to avoid repeating content

1.5 (2015-08-18)
~~~~~~~~~~~~~~~~

* Replaced custom hook for setting environemnt section with a fixture

1.4 (2015-08-12)
~~~~~~~~~~~~~~~~

* Dropped support for pytest 2.6
* Fixed unencodable strings for Python 3
  (`@The-Compiler <https://github.com/The-Compiler>`_)

1.3.2 (2015-07-27)
~~~~~~~~~~~~~~~~~~

* Prevented additional row if log has no content or there is no extra HTML

1.3.1 (2015-05-26)
~~~~~~~~~~~~~~~~~~

* Fixed encoding issue in Python 3

1.3 (2015-05-26)
~~~~~~~~~~~~~~~~

* Show extra content regardless of test result
* Added support for extra content in JSON format

1.2 (2015-05-20)
~~~~~~~~~~~~~~~~

* Changed default sort order to test result
  (`@The-Compiler <https://github.com/The-Compiler>`_)

1.1 (2015-05-08)
~~~~~~~~~~~~~~~~

* Added Python 3 support

1.0 (2015-04-20)
~~~~~~~~~~~~~~~~

* Initial release

.. _Semantic Versioning: https://semver.org
