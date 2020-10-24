Development
===========

To contribute to `pytest-html` you can use `Pipenv`_ to manage
a python virtual environment and `pre-commit <https://pre-commit.com/>`_ to help you with
styling and formatting.

To setup the virtual environment and pre-commit, run:

.. code-block:: bash

  $ pipenv install --dev
  $ pipenv run pre-commit install

If you're not using `Pipenv`_, to install `pre-commit`, run:

.. code-block:: bash

  $ pip install pre-commit
  $ pre-commit install


Automated Testing
-----------------

All pull requests and merges are tested in `GitHub Actions <https://github.com/pytest-dev/pytest-html/actions>`_
which are defined inside ``.github`` folder.

To retrigger CI to run again for a pull request, you either use dropdown
option, close and reopen pull-request or to just update the branch containing
it.

You can do this with `git commit --allow-empty`

Running Tests
-------------

You will need `Tox <https://tox.readthedocs.io>`_ installed to run the tests
against the supported Python versions. If you're using `Pipenv`_ it will be
installed for you.

With `Pipenv`_, run:

.. code-block:: bash

  $ pipenv run tox

Otherwise, to install and run, do:

.. code-block:: bash

  $ pip install tox
  $ tox

Releasing a new version
-----------------------

Follow these steps to release a new version of the project:

1. Update your local master with the upstream master (``git pull --rebase upstream master``)
2. Create a new branch and update ``CHANGES.rst`` with the new version, today's date, and all changes/new features
3. Commit and push the new branch and then create a new pull request
4. Wait for tests and reviews and then merge the branch
5. Once merged, update your local master again (``git pull --rebase upstream master``)
6. Tag the release with the new release version (``git tag v<new tag>``)
7. Push the tag (``git push upstream --tags``)
8. Done. Check `CI <https://github.com/pytest-dev/pytest-html/actions>`_ for release progress.

.. _Pipenv: https://pipenv.pypa.io/en/latest/
