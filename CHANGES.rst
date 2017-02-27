Release Notes
-------------

**1.14.0 (unreleased)**

* Add hooks for modifying the test results table
* Replace environment section with values from
  `pytest-metadata <https://pypi.python.org/pypi/pytest-metadata/>`_
* Fix encoding for asset files
* Escape contents of log sections

**1.13.0 (2016-12-19)**

* Disable ANSI codes support by default due to dependency on
  `ansi2html <https://pypi.python.org/pypi/ansi2html/>`_ package with less
  permissive licensing

**1.12.0 (2016-11-30)**

* Add support for JPG and SVG images
  (`@bhzunami <https://github.com/bhzunami>`_)
* Add version number and PyPI link to report header
  (`@denisra <https://github.com/denisra>`_)

**1.11.1 (2016-11-25)**

* Fix title of checkbox disappearing when unchecked
  (`@vashirov <https://github.com/vashirov>`_)

**1.11.0 (2016-11-08)**

* Add support for ANSI codes in logs
  (`@premkarat <https://github.com/premkarat>`_)

**1.10.1 (2016-09-23)**

* Fix corrupt image asset files
* Remove image links from self-contained report
* Fix issue with unexpected passes not being reported in pytest 3.0

**1.10.0 (2016-08-09)**

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

**1.9.0 (2016-07-04)**

* Split pytest_sessionfinish into generate and save methods
  (`@karandesai-96 <https://github.com/karandesai-96>`_)
* Show tests rerun by pytest-rerunfailures plugin
  (`@RibeiroAna <https://github.com/RibeiroAna>`_)
* Added a feature to filter tests by outcome
  (`@RibeiroAna <https://github.com/RibeiroAna>`_)

**1.8.1 (2016-05-24)**

* Include captured output for passing tests

**1.8.0 (2016-02-24)**

* Remove duplication from the environment section
* Dropped support for Python 3.2
* Indicated setup and teardown in report
* Fixed colour of errors in report

**1.7 (2015-10-19)**

* Fixed INTERNALERROR when an xdist slave crashes
  (`@The-Compiler <https://github.com/The-Compiler>`_)
* Added report sections including stdout and stderr to log

**1.6 (2015-09-08)**

* Fixed environment details when using pytest-xdist

**1.5.1 (2015-08-18)**

* Made environment fixture session scoped to avoid repeating content

**1.5 (2015-08-18)**

* Replaced custom hook for setting environemnt section with a fixture

**1.4 (2015-08-12)**

* Dropped support for pytest 2.6
* Fixed unencodable strings for Python 3
  (`@The-Compiler <https://github.com/The-Compiler>`_)

**1.3.2 (2015-07-27)**

* Prevented additional row if log has no content or there is no extra HTML

**1.3.1 (2015-05-26)**

* Fixed encoding issue in Python 3

**1.3 (2015-05-26)**

* Show extra content regardless of test result
* Added support for extra content in JSON format

**1.2 (2015-05-20)**

* Changed default sort order to test result
  (`@The-Compiler <https://github.com/The-Compiler>`_)

**1.1 (2015-05-08)**

* Added Python 3 support

**1.0 (2015-04-20)**

* Initial release
