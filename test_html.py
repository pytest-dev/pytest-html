# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import re

pytest_plugins = "pytester",


def run(testdir, *args):
    path = testdir.tmpdir.join('report.html')
    result = testdir.runpytest('--html=%s' % path, *args)
    with open(str(path)) as f:
        html = f.read()
    return result, html


def assert_summary(html, tests=1, duration=None, passed=1, skipped=0, failed=0,
                   errors=0, xfailed=0, xpassed=0):
    m = re.search('(\d)+ tests ran in ([\d,.])+ seconds', html)
    assert int(m.group(1)) == tests
    if duration is not None:
        assert float(m.group(2)) >= float(duration)
    assert int(re.search('(\d)+ passed', html).group(1)) == passed
    assert int(re.search('(\d)+ skipped', html).group(1)) == skipped
    assert int(re.search('(\d)+ failed', html).group(1)) == failed
    assert int(re.search('(\d)+ errors', html).group(1)) == errors
    assert int(re.search('(\d)+ expected failures', html).group(1)) == xfailed
    assert int(re.search('(\d)+ unexpected passes', html).group(1)) == xpassed


class TestHTML:

    def test_durations(self, testdir):
        sleep = float(0.1)
        testdir.makepyfile("""
            import time
            def test_sleep():
                time.sleep(%f)
        """ % sleep)
        result, html = run(testdir)
        assert_summary(html, duration=sleep)
        p = re.compile('<td class="col-duration">([\d,.]+)</td>')
        m = p.search(html)
        assert float(m.group(1)) >= sleep

    def test_skip(self, testdir):
        testdir.makepyfile("""
            import pytest
            def test_skip():
                pytest.skip("hello23")
        """)
        result, html = run(testdir)
        assert result.ret == 0
        assert_summary(html, tests=0, passed=0, skipped=1)
        assert 'Skipped: hello23' in html

# report in subdirectory
# resources are present
# additional html works
# links work
# images work
# xfail, xpass, pass, fail, error, skip
