Release Notes
-------------

**1.11.0 (2016-11-08)**

* Add support for ANSI codes in logs

**1.10.1 (2016-09-23)**

* Fix corrupt image asset files
* Remove image links from self-contained report
* Fix issue with unexpected passes not being reported in pytest 3.0

**1.10.0 (2016-08-09)**

* Hide filter checkboxes when JavaScript is disabled
* Removed rerun outcome unless the plugin is active
* Introduce ``--self-contained-html`` option to store CSS and assets inline
* Save images, text, and JSON extras as files in an assets directory
* Use an external CSS file
* Set initial sort order in the HTML
* Allow visibility of extra details to be toggled

**1.9.0 (2016-07-04)**

* Split pytest_sessionfinish into generate and save methods
* Show tests rerun by pytest-rerunfailures plugin
* Added a feature to filter tests by outcome

**1.8.1 (2016-05-24)**

* Include captured output for passing tests

**1.8.0 (2016-02-24)**

* Remove duplication from the environment section
* Dropped support for Python 3.2
* Indicated setup and teardown in report
* Fixed colour of errors in report

**1.7 (2015-10-19)**

* Fixed INTERNALERROR when an xdist slave crashes
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

**1.3.2 (2015-07-27)**

* Prevented additional row if log has no content or there is no extra HTML

**1.3.1 (2015-05-26)**

* Fixed encoding issue in Python 3

**1.3 (2015-05-26)**

* Show extra content regardless of test result
* Added support for extra content in JSON format

**1.2 (2015-05-20)**

* Changed default sort order to test result

**1.1 (2015-05-08)**

* Added Python 3 support

**1.0 (2015-04-20)**

* Initial release
