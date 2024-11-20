Development
===========

To contribute to `pytest-html` you can use `Hatch`_ to manage a python virtual environment and
`pre-commit`_ to help you with styling and formatting.

To setup the virtual environment and pre-commit, run:

.. code-block:: bash

  $ hatch -e test run pre-commit install

If you're not using `Hatch`_, run the following to install `pre-commit`_:

.. code-block:: bash

  $ pip install pre-commit
  $ pre-commit install


Automated Testing
-----------------

All pull requests and merges are tested in `GitHub Actions`_ which are defined inside ``.github`` folder.

To retrigger CI to run again for a pull request, you either use dropdown option, close and reopen pull-request
or to just update the branch containing it.

You can do this with `git commit --allow-empty`

Running Tests
-------------

Python
~~~~~~

You will need `Tox`_ and `Docker`_ installed to run the tests against the supported Python versions. If you're using `Hatch`_
it will be installed for you.

The integration tests requires `Docker`_ as we have to render the report.
This is then done using `Selenium`_ and `BeautifulSoup`_

To start the image needed, run:

.. code-block:: bash

  $ ./start

Sometimes the image becomes unresponsive and needs a restart:

.. code-block:: bash

  $ ./start down && ./start

You can watch the tests in your browser at `localhost:7900`, the password is `secret`.

To run the tests with `Hatch`_, run:

.. code-block:: bash

  $ hatch -e test run tox

Otherwise, to install and run, do:

.. code-block:: bash

  $ pip install tox
  $ tox

JavaScript
~~~~~~~~~~

You will need `npm`_ installed to run the JavaScript tests. Internally, we use `Mocha`_, `Chai`_, `Sinon`_ to run the tests.

Once `npm`_ is installed, you can install all needed dependencies by running:

.. code-block:: bash

  $ npm install

Run the following to execute the tests:

.. code-block:: bash

  $ npm run unit

Documentation
-------------

Documentation is hosted on `Read the Docs`_, and is written in `RST`_. Remember to add any new files to the :code:`toctree`
section in :code:`index.rst`.

To build your documentation, run:

.. code-block:: bash

  $ tox -e docs

You can then run a local webserver to verify your changes compiled correctly.

SASS/SCSS/CSS
-------------

You will need `npm`_ installed to compile the CSS, which is generated via `SASS/SCSS`_.

Once `npm`_ is installed, you can install all needed dependencies by running:

.. code-block:: bash

  $ npm install

Run the following to build the application:

.. code-block:: bash

  $ npm run build

Releasing a new version
-----------------------

Follow these steps to release a new version of the project:

#.  Update your local master with the upstream master (``git pull --rebase upstream master``)
#.  Create a new branch
#.  Update `the changelog`_ with the new version, today's date, and all changes/new features
#.  Commit and push the new branch and then create a new pull request
#.  Wait for tests and reviews and then merge the branch
#.  Once merged, update your local master again (``git pull --rebase upstream master``)
#.  Tag the release with the new release version (``git tag <new tag>``)
#.  Push the tag (``git push upstream --tags``)
#. Done. Check `Github Actions`_ for release progress.

.. _GitHub Actions: https://github.com/pytest-dev/pytest-html/actions
.. _Mocha: https://mochajs.org/
.. _npm: https://www.npmjs.com
.. _Hatch: https://hatch.pypa.io/latest/
.. _pre-commit: https://pre-commit.com
.. _Chai: https://www.chaijs.com/
.. _Sinon: https://sinonjs.org/
.. _Read The Docs: https://readthedocs.com
.. _RST: https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html
.. _SASS/SCSS: https://sass-lang.com
.. _the changelog: https://pytest-html.readthedocs.io/en/latest/changelog.html
.. _Tox: https://tox.readthedocs.io
.. _Docker: https://www.docker.com/
.. _Selenium: https://www.selenium.dev/
.. _BeautifulSoup: https://beautiful-soup-4.readthedocs.io/en/latest/
