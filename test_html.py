# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

pytest_plugins = "pytester",


def runandreturn(testdir, *args):
    path = testdir.tmpdir.join('report.html')
    result = testdir.runpytest('--html=%s' % path, *args)
    with open(str(path)) as f:
        html = f.read()
    return result, html


class TestHTML:
    def test_durations(self, testdir):
        testdir.makepyfile("""
            import time
            def test_sleep():
                time.sleep(1)
        """)
        result, html = runandreturn(testdir)
        assert '1 tests ran in 1 seconds' in html
        assert '1.00' in html  # TODO parse HTML and check greater than sleep

    def test_skip(self, testdir):
        testdir.makepyfile("""
            import pytest
            def test_skip():
                pytest.skip("hello23")
        """)
        result, html = runandreturn(testdir)
        assert result.ret == 0
        assert '0 tests ran' in html
        assert '1 skipped' in html
        assert 'Skipped: hello23' in html

# report in subdirectory
# resources are present
# additional html works
# links work
# images work
# xfail, xpass, pass, fail, error, skip
