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
import hashlib

import pytest

PY3 = sys.version_info[0] == 3
pytest_plugins = "pytester",


def run(testdir, path='report.html', *args):
    path = testdir.tmpdir.join(path)
    result = testdir.runpytest('--html', path, *args)
    with open(str(path)) as f:
        html = f.read()
    return result, html


def assert_results_by_outcome(html, test_outcome, test_outcome_number,
                              label=None):
    # Asserts if the test number of this outcome in the summary is correct
    regex_summary = '(\d)+ {0}'.format(label or test_outcome)
    assert int(re.search(regex_summary, html).group(1)) == test_outcome_number

    # Asserts if the generated checkbox of this outcome is correct
    regex_checkbox = ('<input checked="true" class="filter" '
                      'data-test-result="{0}"'.format(test_outcome))
    if test_outcome_number == 0:
        regex_checkbox += ' disabled="true"'
    assert re.search(regex_checkbox, html) is not None

    # Asserts if the table rows of this outcome are correct
    regex_table = ('tbody class=\"{0} '.format(test_outcome))
    assert len(re.findall(regex_table, html)) == test_outcome_number


def assert_results(html, tests=1, duration=None, passed=1, skipped=0, failed=0,
                   errors=0, xfailed=0, xpassed=0, rerun=0):
    # Asserts total amount of tests
    total_tests = re.search('(\d)+ tests ran', html)
    assert int(total_tests.group(1)) == tests

    # Asserts tests running duration
    if duration is not None:
        tests_duration = re.search('([\d,.])+ seconds', html)
        assert float(tests_duration.group(1)) >= float(duration)

    # Asserts by outcome
    assert_results_by_outcome(html, 'passed', passed)
    assert_results_by_outcome(html, 'skipped', skipped)
    assert_results_by_outcome(html, 'failed', failed)
    assert_results_by_outcome(html, 'error', errors, 'errors')
    assert_results_by_outcome(html, 'xfailed', xfailed, 'expected failures')
    assert_results_by_outcome(html, 'xpassed', xpassed, 'unexpected passes')
    assert_results_by_outcome(html, 'rerun', rerun)


class TestHTML:
    def test_durations(self, testdir):
        sleep = float(0.2)
        testdir.makepyfile("""
            import time
            def test_sleep():
                time.sleep({0:f})
        """.format(sleep * 2))
        result, html = run(testdir)
        assert result.ret == 0
        assert_results(html, duration=sleep)
        p = re.compile('<td class="col-duration">([\d,.]+)</td>')
        m = p.search(html)
        assert float(m.group(1)) >= sleep

    def test_pass(self, testdir):
        testdir.makepyfile('def test_pass(): pass')
        result, html = run(testdir)
        assert result.ret == 0
        assert_results(html)

    def test_skip(self, testdir):
        reason = str(random.random())
        testdir.makepyfile("""
            import pytest
            def test_skip():
                pytest.skip('{0}')
        """.format(reason))
        result, html = run(testdir)
        assert result.ret == 0
        assert_results(html, tests=0, passed=0, skipped=1)
        assert 'Skipped: {0}'.format(reason) in html

    def test_fail(self, testdir):
        testdir.makepyfile('def test_fail(): assert False')
        result, html = run(testdir)
        assert result.ret
        assert_results(html, passed=0, failed=1)
        assert 'AssertionError' in html

    def test_rerun(self, testdir):
        testdir.makepyfile("""
            import pytest
            @pytest.mark.flaky(reruns=5)
            def test_example():
                assert False
        """)
        result, html = run(testdir)
        assert result.ret
        assert_results(html, passed=0, failed=1, rerun=5)

    def test_no_rerun(self, testdir):
        testdir.makepyfile('def test_pass(): pass')
        result, html = run(testdir, 'report.html', '-p', 'no:rerunfailures')
        assert result.ret == 0
        assert re.search('data-test-result="rerun"', html) is None

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
        assert_results(html, tests=4, passed=1, failed=1, xfailed=1, xpassed=1)

    def test_setup_error(self, testdir):
        testdir.makepyfile("""
            def pytest_funcarg__arg(request):
                raise ValueError()
            def test_function(arg):
                pass
        """)
        result, html = run(testdir)
        assert result.ret
        assert_results(html, tests=0, passed=0, errors=1)
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
        assert_results(html, passed=0, xfailed=1)
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
        assert_results(html, passed=0, xpassed=1)

    def test_create_report_path(self, testdir):
        testdir.makepyfile('def test_pass(): pass')
        path = os.path.join('directory', 'report.html')
        result, html = run(testdir, path)
        assert result.ret == 0
        assert_results(html)

    def test_resources_inline_css(self, testdir):
        testdir.makepyfile('def test_pass(): pass')
        result, html = run(testdir, 'report.html', '--self-contained-html')
        assert result.ret == 0

        content = pkg_resources.resource_string(
            'pytest_html', os.path.join('resources', 'style.css'))
        if PY3:
            content = content.decode('utf-8')
        assert content
        assert content in html

    def test_resources(self, testdir):
        testdir.makepyfile('def test_pass(): pass')
        result, html = run(testdir)
        assert result.ret == 0

        content = pkg_resources.resource_string(
            'pytest_html', os.path.join('resources', 'main.js'))
        if PY3:
            content = content.decode('utf-8')
        assert content
        assert content in html
        regex_css_link = '<link href="assets/style.css" rel="stylesheet"'
        assert re.search(regex_css_link, html) is not None

    @pytest.mark.parametrize('result', ['pass', 'fail'])
    def test_stdout(self, testdir, result):
        content = '<spam>ham</spam>'
        escaped = '&lt;spam&gt;ham&lt;/spam&gt;'
        testdir.makepyfile("""
            def test_stdout():
                print('{0}')
                assert '{1}' == 'pass'""".format(content, result))
        _, html = run(testdir)
        assert content not in html
        assert escaped in html

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

    @pytest.mark.parametrize('content, encoded', [
        ("u'\u0081'", 'woE='),
        ("'foo'", 'Zm9v')])
    def test_extra_text(self, testdir, content, encoded):
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
        result, html = run(testdir, 'report.html', '--self-contained-html')
        assert result.ret == 0
        href = 'data:text/plain;charset=utf-8;base64,{0}'.format(encoded)
        link = '<a class="text" href="{0}" target="_blank">Text</a>'.format(
            href)
        assert link in html

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
        result, html = run(testdir, 'report.html', '--self-contained-html')
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

    @pytest.mark.parametrize('mime_type, extension',
                             [('image/png', 'png'),
                              ('image/png', 'image'),
                              ('image/jpeg', 'jpg'),
                              ('image/svg+xml', 'svg')])
    def test_extra_image(self, testdir, mime_type, extension):
        content = str(random.random())
        testdir.makeconftest("""
            import pytest
            @pytest.mark.hookwrapper
            def pytest_runtest_makereport(item, call):
                outcome = yield
                report = outcome.get_result()
                if report.when == 'call':
                    from pytest_html import extras
                    report.extra = [extras.{0}('{1}')]
        """.format(extension, content))
        testdir.makepyfile('def test_pass(): pass')
        result, html = run(testdir, 'report.html', '--self-contained-html')
        assert result.ret == 0
        src = 'data:{0};base64,{1}'.format(mime_type, content)
        assert '<img src="{0}"/>'.format(src) in html

    @pytest.mark.parametrize('content', [("u'\u0081'"), ("'foo'")])
    def test_extra_text_separated(self, testdir, content):
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
        hash_key = ('test_extra_text_separated.py::'
                    'test_pass01').encode('utf-8')
        hash_generator = hashlib.md5()
        hash_generator.update(hash_key)
        assert result.ret == 0
        src = '{0}/{1}'.format('assets', '{0}.txt'.
                               format(hash_generator.hexdigest()))
        link = ('<a class="text" href="{0}" target="_blank">'.format(src))
        assert link in html
        assert os.path.exists(src)

    @pytest.mark.parametrize('file_extension, extra_type', [
        ('png', 'image'),
        ('png', 'png'),
        ('svg', 'svg'),
        ('jpg', 'jpg')])
    def test_extra_image_separated(self, testdir, file_extension, extra_type):
        content = b64encode('foo'.encode('utf-8')).decode('ascii')
        testdir.makeconftest("""
            import pytest
            @pytest.mark.hookwrapper
            def pytest_runtest_makereport(item, call):
                outcome = yield
                report = outcome.get_result()
                if report.when == 'call':
                    from pytest_html import extras
                    report.extra = [extras.{0}('{1}')]
        """.format(extra_type, content))
        testdir.makepyfile('def test_pass(): pass')
        result, html = run(testdir)
        hash_key = ('test_extra_image_separated.py::'
                    'test_pass01').encode('utf-8')
        hash_generator = hashlib.md5()
        hash_generator.update(hash_key)
        assert result.ret == 0
        src = '{0}/{1}'.format('assets', '{0}.{1}'.
                               format(hash_generator.hexdigest(),
                                      file_extension))
        link = ('<a class="image" href="{0}" target="_blank">'.format(src))
        assert link in html
        assert os.path.exists(src)

    @pytest.mark.parametrize('file_extension, extra_type', [
        ('png', 'image'),
        ('png', 'png'),
        ('svg', 'svg'),
        ('jpg', 'jpg')])
    def test_extra_image_separated_rerun(self, testdir, file_extension,
                                         extra_type):
        content = b64encode('foo'.encode('utf-8')).decode('ascii')
        testdir.makeconftest("""
            import pytest
            @pytest.mark.hookwrapper
            def pytest_runtest_makereport(item, call):
                outcome = yield
                report = outcome.get_result()
                if report.when == 'call':
                    from pytest_html import extras
                    report.extra = [extras.{0}('{1}')]
        """.format(extra_type, content))
        testdir.makepyfile("""
            import pytest
            @pytest.mark.flaky(reruns=2)
            def test_fail():
                assert False""")
        result, html = run(testdir)

        for i in range(1, 4):
            hash_key = ('test_extra_image_separated_rerun.py::'
                        'test_fail0{0}'.format(i)).encode('utf-8')
            hash_generator = hashlib.md5()
            hash_generator.update(hash_key)
            src = 'assets/{0}.{1}'.format(hash_generator.hexdigest(),
                                          file_extension)
            link = ('<a class="image" href="{0}" target="_blank">'.format(src))
            assert result.ret
            assert link in html
            assert os.path.exists(src)

    @pytest.mark.parametrize('src_type', ["https://", "file://", "image.png"])
    def test_extra_image_non_b64(self, testdir, src_type):
        content = src_type
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
        if src_type == "image.png":
            testdir.makefile('.png', image='pretty picture')
        result, html = run(testdir, 'report.html')
        assert result.ret == 0
        assert '<a href="{0}"><img src="{0}"/>'.format(content) in html

    def test_no_environment(self, testdir):
        testdir.makeconftest("""
            def pytest_configure(config):
                config._metadata = None
        """)
        testdir.makepyfile('def test_pass(): pass')
        result, html = run(testdir)
        assert result.ret == 0
        assert 'Environment' not in html

    def test_environment(self, testdir):
        content = str(random.random())
        testdir.makeconftest("""
            def pytest_configure(config):
                config._metadata['content'] = '{0}'
        """.format(content))
        testdir.makepyfile('def test_pass(): pass')
        result, html = run(testdir)
        assert result.ret == 0
        assert 'Environment' in html
        assert len(re.findall(content, html)) == 1

    def test_environment_xdist(self, testdir):
        content = str(random.random())
        testdir.makeconftest("""
            def pytest_configure(config):
                for i in range(2):
                    config._metadata['content'] = '{0}'
        """.format(content))
        testdir.makepyfile('def test_pass(): pass')
        result, html = run(testdir, 'report.html', '-n', '1')
        assert result.ret == 0
        assert 'Environment' in html
        assert len(re.findall(content, html)) == 1

    def test_environment_xdist_reruns(self, testdir):
        content = str(random.random())
        testdir.makeconftest("""
            def pytest_configure(config):
                for i in range(2):
                    config._metadata['content'] = '{0}'
        """.format(content))
        testdir.makepyfile('def test_fail(): assert False')
        result, html = run(testdir, 'report.html', '-n', '1', '--reruns', '1')
        assert result.ret
        assert 'Environment' in html
        assert len(re.findall(content, html)) == 1

    @pytest.mark.xfail(
        sys.version_info < (3, 2) and
        LooseVersion(pytest.__version__) >= LooseVersion('2.8.0'),
        reason='Fails on earlier versions of Python and pytest',
        run=False)
    def test_xdist_crashing_slave(self, testdir):
        """https://github.com/pytest-dev/pytest-html/issues/21"""
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
        assert_results(html, passed=1)

    def test_ansi_color(self, testdir):
        try:
            import ansi2html  # NOQA
            ANSI = True
        except ImportError:
            # ansi2html is not installed
            ANSI = False
        pass_content = ["<span class=\"ansi31\">RCOLOR",
                        "<span class=\"ansi32\">GCOLOR",
                        "<span class=\"ansi33\">YCOLOR"]
        testdir.makepyfile(r"""
            def test_ansi():
                colors = ['\033[31mRCOLOR\033[0m', '\033[32mGCOLOR\033[0m',
                          '\033[33mYCOLOR\033[0m']
                for color in colors:
                    print(color)
        """)
        result, html = run(testdir, 'report.html', '--self-contained-html')
        assert result.ret == 0
        for content in pass_content:
            if ANSI:
                assert content in html
            else:
                assert content not in html

    @pytest.mark.parametrize('content', [("'foo'"), ("u'\u0081'")])
    def test_utf8_longrepr(self, testdir, content):
        testdir.makeconftest("""
            import pytest
            @pytest.mark.hookwrapper
            def pytest_runtest_makereport(item, call):
                outcome = yield
                report = outcome.get_result()
                if report.when == 'call':
                    report.longrepr = 'utf8 longrepr: ' + {0}
        """.format(content))
        testdir.makepyfile("""
            def test_fail():
                testtext = 'utf8 longrepr: '
                assert False
        """)
        result, html = run(testdir, 'report.html', '--self-contained-html')
        assert result.ret
        assert 'utf8 longrepr' in html
