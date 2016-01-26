Release Notes
-------------

**1.8 (unreleased)**

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
