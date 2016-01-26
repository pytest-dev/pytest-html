# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from base64 import b64encode
from distutils.version import LooseVersion
import json
import os
import sys
import pkg_resources
import random
import re

import pytest

PY3 = sys.version_info[0] == 3
pytest_plugins = "pytester",


def run(testdir, path='report.html', *args):
    path = testdir.tmpdir.join(path)
    result = testdir.runpytest('--html', path, *args)
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
                time.sleep({0:f})
        """.format(sleep))
        result, html = run(testdir)
        assert result.ret == 0
        assert_summary(html, duration=sleep)
        p = re.compile('<td class="col-duration">([\d,.]+)</td>')
        m = p.search(html)
        assert float(m.group(1)) >= sleep

    def test_pass(self, testdir):
        testdir.makepyfile('def test_pass(): pass')
        result, html = run(testdir)
        assert result.ret == 0
        assert_summary(html)

    def test_skip(self, testdir):
        reason = str(random.random())
        testdir.makepyfile("""
            import pytest
            def test_skip():
                pytest.skip('{0}')
        """.format(reason))
        result, html = run(testdir)
        assert result.ret == 0
        assert_summary(html, tests=0, passed=0, skipped=1)
        assert 'Skipped: {0}'.format(reason) in html

    def test_fail(self, testdir):
        testdir.makepyfile('def test_fail(): assert False')
        result, html = run(testdir)
        assert result.ret
        assert_summary(html, passed=0, failed=1)
        assert 'AssertionError' in html

    def test_conditional_xfails(self, testdir):
        testdir.makepyfile("""
            import pytest
            @pytest.mark.xfail(False, reason='reason')
            def test_fail(): assert False
            @pytest.mark.xfail(False, reason='reason')
            def test_pass(): pass
            @pytest.mark.xfail(True, reason='reason')
            def test_xfail(): assert False
            @pytest.mark.xfail(True, reason='reason')
            def test_xpass(): pass
        """)
        result, html = run(testdir)
        assert result.ret
        assert_summary(html, tests=4, passed=1, failed=1, xfailed=1, xpassed=1)

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
        assert '::setup' in html
        assert 'ValueError' in html

    def test_xfail(self, testdir):
        reason = str(random.random())
        testdir.makepyfile("""
            import pytest
            def test_xfail():
                pytest.xfail('{0}')
        """.format(reason))
        result, html = run(testdir)
        assert result.ret == 0
        assert_summary(html, passed=0, xfailed=1)
        assert 'XFailed: {0}'.format(reason) in html

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
        testdir.makepyfile('def test_pass(): pass')
        path = os.path.join('directory', 'report.html')
        result, html = run(testdir, path)
        assert result.ret == 0
        assert_summary(html)

    def test_resources(self, testdir):
        testdir.makepyfile('def test_pass(): pass')
        result, html = run(testdir)
        assert result.ret == 0
        for resource in ['style.css', 'main.js']:
            content = pkg_resources.resource_string(
                'pytest_html', os.path.join('resources', resource))
            if PY3:
                content = content.decode('utf-8')
            assert content
            assert content in html

    def test_stdout(self, testdir):
        content = str(random.random())
        testdir.makepyfile("""
            def test_fail():
                print({0})
                assert False""".format(content))
        result, html = run(testdir)
        assert result.ret
        assert content in html

    def test_extra_html(self, testdir):
        content = str(random.random())
        testdir.makeconftest("""
            import pytest
            @pytest.mark.hookwrapper
            def pytest_runtest_makereport(item, call):
                outcome = yield
                report = outcome.get_result()
                if report.when == 'call':
                    from pytest_html import extras
                    report.extra = [extras.html('<div>{0}</div>')]
        """.format(content))
        testdir.makepyfile('def test_pass(): pass')
        result, html = run(testdir)
        assert result.ret == 0
        assert content in html

    def test_extra_text(self, testdir):
        content = str(random.random())
        testdir.makeconftest("""
            import pytest
            @pytest.mark.hookwrapper
            def pytest_runtest_makereport(item, call):
                outcome = yield
                report = outcome.get_result()
                if report.when == 'call':
                    from pytest_html import extras
                    report.extra = [extras.text('{0}')]
        """.format(content))
        testdir.makepyfile('def test_pass(): pass')
        result, html = run(testdir)
        assert result.ret == 0
        if PY3:
            data = b64encode(content.encode('utf-8')).decode('ascii')
        else:
            data = b64encode(content)
        href = 'data:text/plain;charset=utf-8;base64,{0}'.format(data)
        link = '<a class="text" href="{0}" target="_blank">Text</a>'.format(
            href)
        assert link in html

    @pytest.mark.xfail(
        sys.version_info < (3, 2),
        reason='Only affects Python versions later than 3.2',
        run=False)
    def test_extra_bytes(self, testdir):
        content = bytes(str(random.random()), 'utf-8')
        testdir.makeconftest("""
            import pytest
            @pytest.mark.hookwrapper
            def pytest_runtest_makereport(item, call):
                outcome = yield
                report = outcome.get_result()
                if report.when == 'call':
                    from pytest_html import extras
                    report.extra = [extras.text({0})]
        """.format(content))
        testdir.makepyfile('def test_pass(): pass')
        result, html = run(testdir)
        assert result.ret == 0
        data = b64encode(content).decode('ascii')
        href = 'data:text/plain;charset=utf-8;base64,{0}'.format(data)
        link = '<a class="text" href="{0}" target="_blank">Text</a>'.format(
            href)
        assert link in html

    def test_extra_url(self, testdir):
        content = str(random.random())
        testdir.makeconftest("""
            import pytest
            @pytest.mark.hookwrapper
            def pytest_runtest_makereport(item, call):
                outcome = yield
                report = outcome.get_result()
                if report.when == 'call':
                    from pytest_html import extras
                    report.extra = [extras.url('{0}')]
        """.format(content))
        testdir.makepyfile('def test_pass(): pass')
        result, html = run(testdir)
        assert result.ret == 0
        link = '<a class="url" href="{0}" target="_blank">URL</a>'.format(
            content)
        assert link in html

    def test_extra_image(self, testdir):
        content = str(random.random())
        testdir.makeconftest("""
            import pytest
            @pytest.mark.hookwrapper
            def pytest_runtest_makereport(item, call):
                outcome = yield
                report = outcome.get_result()
                if report.when == 'call':
                    from pytest_html import extras
                    report.extra = [extras.image('{0}')]
        """.format(content))
        testdir.makepyfile('def test_pass(): pass')
        result, html = run(testdir)
        assert result.ret == 0
        assert '<a class="image" href="#" target="_blank">Image</a>' in html
        src = 'data:image/png;base64,{0}'.format(content)
        assert '<a href="#"><img src="{0}"/></a>'.format(src) in html

    def test_extra_json(self, testdir):
        content = {str(random.random()): str(random.random())}
        testdir.makeconftest("""
            import pytest
            @pytest.mark.hookwrapper
            def pytest_runtest_makereport(item, call):
                outcome = yield
                report = outcome.get_result()
                if report.when == 'call':
                    from pytest_html import extras
                    report.extra = [extras.json({0})]
        """.format(content))
        testdir.makepyfile('def test_pass(): pass')
        result, html = run(testdir)
        assert result.ret == 0
        content_str = json.dumps(content)
        if PY3:
            data = b64encode(content_str.encode('utf-8')).decode('ascii')
        else:
            data = b64encode(content_str)
        href = 'data:application/json;charset=utf-8;base64,{0}'.format(data)
        link = '<a class="json" href="{0}" target="_blank">JSON</a>'.format(
            href)
        assert link in html

    def test_no_environment(self, testdir):
        testdir.makeconftest("""
            import pytest
            @pytest.fixture(autouse=True)
            def _environment(request):
                request.config._environment = None
        """)
        testdir.makepyfile('def test_pass(): pass')
        result, html = run(testdir)
        assert result.ret == 0
        assert 'Environment' not in html

    def test_environment(self, testdir):
        content = (str(random.random()), str(random.random()))
        testdir.makeconftest("""
            import pytest
            @pytest.fixture(autouse=True)
            def _environment(request):
                request.config._environment.append(('{0[0]}', '{0[1]}'))
        """.format(content))
        testdir.makepyfile('def test_pass(): pass')
        result, html = run(testdir)
        assert result.ret == 0
        assert 'Environment' in html
        for c in content:
            assert c in html

    def test_environment_xdist(self, testdir):
        content = (str(random.random()), str(random.random()))
        testdir.makeconftest("""
            import pytest
            @pytest.fixture(autouse=True)
            def _environment(request):
                request.config._environment.append(('{0[0]}', '{0[1]}'))
        """.format(content))
        testdir.makepyfile('def test_pass(): pass')
        result, html = run(testdir, 'report.html', '-n', '1')
        assert result.ret == 0
        assert 'Environment' in html
        for c in content:
            assert c in html

    @pytest.mark.xfail(
        sys.version_info < (3, 2) and
        LooseVersion(pytest.__version__) >= LooseVersion('2.8.0'),
        reason='Fails on earlier versions of Python and pytest',
        run=False)
    def test_xdist_crashing_slave(self, testdir):
        """https://github.com/davehunt/pytest-html/issues/21"""
        testdir.makepyfile("""
            import os
            def test_exit():
                os._exit(0)
        """)
        result, html = run(testdir, 'report.html', '-n', '1')
        assert 'INTERNALERROR>' not in result.stdout.str()

    def test_utf8_surrogate(self, testdir):
        testdir.makepyfile(r"""
            import pytest

            @pytest.mark.parametrize('val', ['\ud800'])
            def test_foo(val):
                pass
        """)
        result, html = run(testdir)
        assert result.ret == 0
        assert_summary(html, passed=1)
