# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from base64 import b64encode
import os
import sys
import pkg_resources
import random
import re

PY3 = sys.version_info[0] == 3
pytest_plugins = "pytester",


def run(testdir, path='report.html', *args):
    path = testdir.tmpdir.join(path)
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
        sleep = float(0.2)
        testdir.makepyfile("""
            import time
            def test_sleep():
                time.sleep(%f)
        """ % sleep)
        result, html = run(testdir)
        assert result.ret == 0
        assert_summary(html, duration=sleep)
        p = re.compile('<td class="col-duration">([\d,.]+)</td>')
        m = p.search(html)
        assert float(m.group(1)) >= sleep

    def test_pass(self, testdir):
        testdir.makepyfile("def test_pass(): pass")
        result, html = run(testdir)
        assert result.ret == 0
        assert_summary(html)

    def test_skip(self, testdir):
        reason = str(random.random())
        testdir.makepyfile("""
            import pytest
            def test_skip():
                pytest.skip("%s")
        """ % reason)
        result, html = run(testdir)
        assert result.ret == 0
        assert_summary(html, tests=0, passed=0, skipped=1)
        assert 'Skipped: %s' % reason in html

    def test_fail(self, testdir):
        testdir.makepyfile("def test_fail(): assert False")
        result, html = run(testdir)
        assert result.ret
        assert_summary(html, passed=0, failed=1)
        assert 'AssertionError' in html

    def test_setup_error(self, testdir):
        testdir.makepyfile("""
            def pytest_funcarg__arg(request):
                raise ValueError()
            def test_function(arg):
                pass
        """)
        result, html = run(testdir)
        assert result.ret
        assert_summary(html, tests=0, passed=0, errors=1)
        assert 'ValueError' in html

    def test_xfail(self, testdir):
        reason = str(random.random())
        testdir.makepyfile("""
            import pytest
            def test_xfail():
                pytest.xfail("%s")
        """ % reason)
        result, html = run(testdir)
        assert result.ret == 0
        assert_summary(html, passed=0, xfailed=1)
        assert 'XFailed: %s' % reason in html

    def test_xpass(self, testdir):
        testdir.makepyfile("""
            import pytest
            @pytest.mark.xfail()
            def test_xpass():
                pass
        """)
        result, html = run(testdir)
        assert result.ret == 0
        assert_summary(html, passed=0, xpassed=1)

    def test_create_report_path(self, testdir):
        testdir.makepyfile("def test_pass(): pass")
        path = os.path.join('directory', 'report.html')
        result, html = run(testdir, path)
        assert result.ret == 0
        assert_summary(html)

    def test_resources(self, testdir):
        testdir.makepyfile("def test_pass(): pass")
        result, html = run(testdir)
        assert result.ret == 0
        for resource in ['style.css', 'main.js']:
            content = pkg_resources.resource_string(
                'pytest_html', os.path.join('resources', resource))
            assert content
            assert content in html

    def test_extra_html(self, testdir):
        content = str(random.random())
        testdir.makeconftest("""
            def pytest_runtest_makereport(__multicall__, item):
                report = __multicall__.execute()
                if report.when == 'call':
                    from py.xml import html
                    from pytest_html import extras
                    report.extra = [extras.html(html.div(%s))]
                return report
        """ % content)
        testdir.makepyfile("def test_fail(): assert False")
        result, html = run(testdir)
        assert result.ret
        assert content in html

    def test_extra_text(self, testdir):
        content = str(random.random())
        testdir.makeconftest("""
            def pytest_runtest_makereport(__multicall__, item):
                report = __multicall__.execute()
                if report.when == 'call':
                    from pytest_html import extras
                    report.extra = [extras.text('%s')]
                return report
        """ % content)
        testdir.makepyfile("def test_fail(): assert False")
        result, html = run(testdir)
        assert result.ret
        href = 'data:text/plain;charset=utf-8;base64,%s' % b64encode(content)
        link = '<a class="text" href="%s" target="_blank">Text</a>' % href
        assert link in html

    def test_extra_url(self, testdir):
        content = str(random.random())
        testdir.makeconftest("""
            def pytest_runtest_makereport(__multicall__, item):
                report = __multicall__.execute()
                if report.when == 'call':
                    from pytest_html import extras
                    report.extra = [extras.url('%s')]
                return report
        """ % content)
        testdir.makepyfile("def test_fail(): assert False")
        result, html = run(testdir)
        assert result.ret
        link = '<a class="url" href="%s" target="_blank">URL</a>' % content
        assert link in html

    def test_extra_image(self, testdir):
        content = str(random.random())
        testdir.makeconftest("""
            def pytest_runtest_makereport(__multicall__, item):
                report = __multicall__.execute()
                if report.when == 'call':
                    from pytest_html import extras
                    report.extra = [extras.image('%s')]
                return report
        """ % content)
        testdir.makepyfile("def test_fail(): assert False")
        result, html = run(testdir)
        assert result.ret
        assert '<a class="image" href="#" target="_blank">Image</a>' in html
        src = 'data:image/png;base64,%s' % content
        assert '<a href="#"><img src="%s"/></a>' % src in html

    def test_no_environment(self, testdir):
        testdir.makepyfile("def test_pass(): pass")
        result, html = run(testdir)
        assert result.ret == 0
        assert 'Environment' not in html

    def test_environment(self, testdir):
        content = (str(random.random()), str(random.random()))
        testdir.makeconftest("""
            def pytest_html_environment(config):
                return {'%s': %s}
        """ % content)
        testdir.makepyfile("def test_pass(): pass")
        result, html = run(testdir)
        assert result.ret == 0
        assert 'Environment' in html
        for c in content:
            assert c in html
