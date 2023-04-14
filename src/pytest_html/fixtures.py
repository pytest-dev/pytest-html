# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import warnings

import pytest

extras_stash_key = pytest.StashKey[list]()


@pytest.fixture
def extra(pytestconfig):
    """DEPRECATED: Add details to the HTML reports.

    .. code-block:: python

        import pytest_html


        def test_foo(extra):
            extra.append(pytest_html.extras.url("https://www.example.com/"))
    """
    warnings.warn(
        "The 'extra' fixture is deprecated and will be removed in a future release"
        ", use 'extras' instead.",
        DeprecationWarning,
    )
    pytestconfig.stash[extras_stash_key] = []
    yield pytestconfig.stash[extras_stash_key]
    del pytestconfig.stash[extras_stash_key][:]


@pytest.fixture
def extras(pytestconfig):
    """Add details to the HTML reports.

    .. code-block:: python

        import pytest_html


        def test_foo(extras):
            extras.append(pytest_html.extras.url("https://www.example.com/"))
    """
    pytestconfig.stash[extras_stash_key] = []
    yield pytestconfig.stash[extras_stash_key]
    del pytestconfig.stash[extras_stash_key][:]
