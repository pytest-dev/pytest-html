# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from base64 import b64encode
import json
import os
import pkg_resources
import random
import re

import pytest

pytest_plugins = ("pytester",)


def run(testdir, path="report.html", *args):
    path = testdir.tmpdir.join(path)
    result = testdir.runpytest("--html", path, *args)
    return result, read_html(path)


def read_html(path):
    with open(str(path)) as f:
        return f.read()


def assert_results_by_outcome(html, test_outcome, test_outcome_number, label=None):
    # Asserts if the test number of this outcome in the summary is correct
    regex_summary = r"(\d)+ {}".format(label or test_outcome)
    assert int(re.search(regex_summary, html).group(1)) == test_outcome_number

    # Asserts if the generated checkbox of this outcome is correct
    regex_checkbox = (
        f'<input checked="true" class="filter" data-test-result="{test_outcome}"'
    )
    if test_outcome_number == 0:
        regex_checkbox += ' disabled="true"'
    assert re.search(regex_checkbox, html) is not None

    # Asserts if the table rows of this outcome are correct
    regex_table = f'tbody class="{test_outcome} '
    assert len(re.findall(regex_table, html)) == test_outcome_number


def assert_results(
    html,
    tests=1,
    duration=None,
    passed=1,
    skipped=0,
    failed=0,
    errors=0,
    xfailed=0,
    xpassed=0,
    rerun=0,
):
    # Asserts total amount of tests
    total_tests = re.search(r"(\d)+ tests ran", html)
    assert int(total_tests.group(1)) == tests

    # Asserts tests running duration
    if duration is not None:
        tests_duration = re.search(r"([\d,.]+) seconds", html)
        assert float(tests_duration.group(1)) >= float(duration)

    # Asserts by outcome
    assert_results_by_outcome(html, "passed", passed)
    assert_results_by_outcome(html, "skipped", skipped)
    assert_results_by_outcome(html, "failed", failed)
    assert_results_by_outcome(html, "error", errors, "errors")
    assert_results_by_outcome(html, "xfailed", xfailed, "expected failures")
    assert_results_by_outcome(html, "xpassed", xpassed, "unexpected passes")
    assert_results_by_outcome(html, "rerun", rerun)


class TestHTML:
    def test_durations(self, testdir):
        sleep = float(0.2)
        testdir.makepyfile(
            """
            import time
            def test_sleep():
                time.sleep({:f})
        """.format(
                sleep * 2
            )
        )
        result, html = run(testdir)
        assert result.ret == 0
        assert_results(html, duration=sleep)
        p = re.compile(r'<td class="col-duration">([\d,.]+)</td>')
        m = p.search(html)
        assert float(m.group(1)) >= sleep

    def test_pass(self, testdir):
        testdir.makepyfile("def test_pass(): pass")
        result, html = run(testdir)
        assert result.ret == 0
        assert_results(html)

    def test_skip(self, testdir):
        reason = str(random.random())
        testdir.makepyfile(
            f"""
            import pytest
            def test_skip():
                pytest.skip('{reason}')
        """
        )
        result, html = run(testdir)
        assert result.ret == 0
        assert_results(html, tests=0, passed=0, skipped=1)
        assert f"Skipped: {reason}" in html

    def test_fail(self, testdir):
        testdir.makepyfile("def test_fail(): assert False")
        result, html = run(testdir)
        assert result.ret
        assert_results(html, passed=0, failed=1)
        assert "AssertionError" in html

    def test_rerun(self, testdir):
        testdir.makepyfile(
            """
            import pytest
            @pytest.mark.flaky(reruns=5)
            def test_example():
                assert False
        """
        )
        result, html = run(testdir)
        assert result.ret
        assert_results(html, passed=0, failed=1, rerun=5)

    def test_no_rerun(self, testdir):
        testdir.makepyfile("def test_pass(): pass")
        result, html = run(testdir, "report.html", "-p", "no:rerunfailures")
        assert result.ret == 0
        assert re.search('data-test-result="rerun"', html) is None

    def test_conditional_xfails(self, testdir):
        testdir.makepyfile(
            """
            import pytest
            @pytest.mark.xfail(False, reason='reason')
            def test_fail(): assert False
            @pytest.mark.xfail(False, reason='reason')
            def test_pass(): pass
            @pytest.mark.xfail(True, reason='reason')
            def test_xfail(): assert False
            @pytest.mark.xfail(True, reason='reason')
            def test_xpass(): pass
        """
        )
        result, html = run(testdir)
        assert result.ret
        assert_results(html, tests=4, passed=1, failed=1, xfailed=1, xpassed=1)

    def test_setup_error(self, testdir):
        testdir.makepyfile(
            """
            import pytest
            @pytest.fixture
            def arg(request):
                raise ValueError()
            def test_function(arg):
                pass
        """
        )
        result, html = run(testdir)
        assert result.ret
        assert_results(html, tests=0, passed=0, errors=1)
        assert "::setup" in html
        assert "ValueError" in html

    def test_xfail(self, testdir):
        reason = str(random.random())
        testdir.makepyfile(
            f"""
            import pytest
            def test_xfail():
                pytest.xfail('{reason}')
        """
        )
        result, html = run(testdir)
        assert result.ret == 0
        assert_results(html, passed=0, xfailed=1)
        assert f"XFailed: {reason}" in html

    def test_xpass(self, testdir):
        testdir.makepyfile(
            """
            import pytest
            @pytest.mark.xfail()
            def test_xpass():
                pass
        """
        )
        result, html = run(testdir)
        assert result.ret == 0
        assert_results(html, passed=0, xpassed=1)

    def test_create_report_path(self, testdir):
        testdir.makepyfile("def test_pass(): pass")
        path = os.path.join("directory", "report.html")
        result, html = run(testdir, path)
        assert result.ret == 0
        assert_results(html)

    @pytest.mark.parametrize("path", ["", "directory"])
    def test_report_title(self, testdir, path):
        testdir.makepyfile("def test_pass(): pass")
        report_name = "report.html"
        path = os.path.join(path, report_name)
        result, html = run(testdir, path)
        assert result.ret == 0
        report_title = f"<h1>{report_name}</h1>"
        assert report_title in html

    def test_report_title_addopts_env_var(self, testdir, monkeypatch):
        report_location = "REPORT_LOCATION"
        report_name = "MuhReport"
        monkeypatch.setenv(report_location, report_name)
        testdir.makefile(
            ".ini",
            pytest=f"""
            [pytest]
            addopts = --html ${report_location}
        """,
        )
        testdir.makepyfile("def test_pass(): pass")
        result = testdir.runpytest()
        assert result.ret == 0
        report_title = f"<h1>{report_name}</h1>"
        assert report_title in read_html(report_name)

    def test_resources_inline_css(self, testdir):
        testdir.makepyfile("def test_pass(): pass")
        result, html = run(testdir, "report.html", "--self-contained-html")
        assert result.ret == 0

        content = pkg_resources.resource_string(
            "pytest_html", os.path.join("resources", "style.css")
        )
        content = content.decode("utf-8")
        assert content
        assert content in html

    def test_resources(self, testdir):
        testdir.makepyfile("def test_pass(): pass")
        result, html = run(testdir)
        assert result.ret == 0

        content = pkg_resources.resource_string(
            "pytest_html", os.path.join("resources", "main.js")
        )
        content = content.decode("utf-8")
        assert content
        assert content in html
        regex_css_link = '<link href="assets/style.css" rel="stylesheet"'
        assert re.search(regex_css_link, html) is not None

    @pytest.mark.parametrize("result", ["pass", "fail"])
    def test_stdout(self, testdir, result):
        content = "<spam>ham</spam>"
        escaped = "&lt;spam&gt;ham&lt;/spam&gt;"
        testdir.makepyfile(
            f"""
            def test_stdout():
                print('{content}')
                assert f'{result}' == 'pass'"""
        )
        _, html = run(testdir)
        assert content not in html
        assert escaped in html

    def test_custom_content_in_summary(self, testdir):
        content_prefix = str(random.random())
        content_summary = str(random.random())
        content_suffix = str(random.random())
        testdir.makeconftest(
            f"""
            import pytest
            from py.xml import html

            def pytest_html_results_summary(prefix, summary, postfix):
                prefix.append(html.p("prefix is {content_prefix}"))
                summary.extend([html.p("extra summary is {content_summary}")])
                postfix.extend([html.p("postfix is {content_suffix}")])
        """
        )
        testdir.makepyfile("def test_pass(): pass")
        result, html = run(testdir)
        assert result.ret == 0
        assert len(re.findall(content_prefix, html)) == 1
        assert len(re.findall(content_summary, html)) == 1
        assert len(re.findall(content_suffix, html)) == 1

    def test_extra_html(self, testdir):
        content = str(random.random())
        testdir.makeconftest(
            f"""
            import pytest
            @pytest.hookimpl(hookwrapper=True)
            def pytest_runtest_makereport(item, call):
                outcome = yield
                report = outcome.get_result()
                if report.when == 'call':
                    from pytest_html import extras
                    report.extra = [extras.html('<div>{content}</div>')]
        """
        )
        testdir.makepyfile("def test_pass(): pass")
        result, html = run(testdir)
        assert result.ret == 0
        assert content in html

    @pytest.mark.parametrize(
        "content, encoded",
        [("u'\u0081'", "woE="), ("'foo'", "Zm9v"), ("b'\\xe2\\x80\\x93'", "4oCT")],
    )
    def test_extra_text(self, testdir, content, encoded):
        testdir.makeconftest(
            f"""
            import pytest
            @pytest.hookimpl(hookwrapper=True)
            def pytest_runtest_makereport(item, call):
                outcome = yield
                report = outcome.get_result()
                if report.when == 'call':
                    from pytest_html import extras
                    report.extra = [extras.text({content})]
        """
        )
        testdir.makepyfile("def test_pass(): pass")
        result, html = run(testdir, "report.html", "--self-contained-html")
        assert result.ret == 0
        href = f"data:text/plain;charset=utf-8;base64,{encoded}"
        link = f'<a class="text" href="{href}" target="_blank">Text</a>'
        assert link in html

    def test_extra_json(self, testdir):
        content = {str(random.random()): str(random.random())}
        testdir.makeconftest(
            f"""
            import pytest
            @pytest.hookimpl(hookwrapper=True)
            def pytest_runtest_makereport(item, call):
                outcome = yield
                report = outcome.get_result()
                if report.when == 'call':
                    from pytest_html import extras
                    report.extra = [extras.json({content})]
        """
        )
        testdir.makepyfile("def test_pass(): pass")
        result, html = run(testdir, "report.html", "--self-contained-html")
        assert result.ret == 0
        content_str = json.dumps(content)
        data = b64encode(content_str.encode("utf-8")).decode("ascii")
        href = f"data:application/json;charset=utf-8;base64,{data}"
        link = f'<a class="json" href="{href}" target="_blank">JSON</a>'
        assert link in html

    def test_extra_url(self, testdir):
        content = str(random.random())
        testdir.makeconftest(
            f"""
            import pytest
            @pytest.hookimpl(hookwrapper=True)
            def pytest_runtest_makereport(item, call):
                outcome = yield
                report = outcome.get_result()
                if report.when == 'call':
                    from pytest_html import extras
                    report.extra = [extras.url('{content}')]
        """
        )
        testdir.makepyfile("def test_pass(): pass")
        result, html = run(testdir)
        assert result.ret == 0
        link = f'<a class="url" href="{content}" target="_blank">URL</a>'
        assert link in html

    @pytest.mark.parametrize(
        "mime_type, extension",
        [
            ("image/png", "png"),
            ("image/png", "image"),
            ("image/jpeg", "jpg"),
            ("image/svg+xml", "svg"),
        ],
    )
    def test_extra_image(self, testdir, mime_type, extension):
        content = str(random.random())
        testdir.makeconftest(
            f"""
            import pytest
            @pytest.hookimpl(hookwrapper=True)
            def pytest_runtest_makereport(item, call):
                outcome = yield
                report = outcome.get_result()
                if report.when == 'call':
                    from pytest_html import extras
                    report.extra = [extras.{extension}('{content}')]
        """
        )
        testdir.makepyfile("def test_pass(): pass")
        result, html = run(testdir, "report.html", "--self-contained-html")
        assert result.ret == 0
        src = f"data:{mime_type};base64,{content}"
        assert f'<img src="{src}"/>' in html

    def test_extra_image_windows(self, mocker, testdir):
        mock_isfile = mocker.patch("pytest_html.plugin.isfile")
        mock_isfile.side_effect = ValueError("stat: path too long for Windows")
        self.test_extra_image(testdir, "image/png", "png")
        assert mock_isfile.call_count == 1

    @pytest.mark.parametrize(
        "content", [("u'\u0081'"), ("'foo'"), ("b'\\xe2\\x80\\x93'")]
    )
    def test_extra_text_separated(self, testdir, content):
        testdir.makeconftest(
            f"""
            import pytest
            @pytest.hookimpl(hookwrapper=True)
            def pytest_runtest_makereport(item, call):
                outcome = yield
                report = outcome.get_result()
                if report.when == 'call':
                    from pytest_html import extras
                    report.extra = [extras.text({content})]
        """
        )
        testdir.makepyfile("def test_pass(): pass")
        result, html = run(testdir)
        assert result.ret == 0
        src = "assets/test_extra_text_separated.py__test_pass_0_0.txt"
        link = f'<a class="text" href="{src}" target="_blank">'
        assert link in html
        assert os.path.exists(src)

    @pytest.mark.parametrize(
        "file_extension, extra_type",
        [("png", "image"), ("png", "png"), ("svg", "svg"), ("jpg", "jpg")],
    )
    def test_extra_image_separated(self, testdir, file_extension, extra_type):
        content = b64encode(b"foo").decode("ascii")
        testdir.makeconftest(
            f"""
            import pytest
            @pytest.hookimpl(hookwrapper=True)
            def pytest_runtest_makereport(item, call):
                outcome = yield
                report = outcome.get_result()
                if report.when == 'call':
                    from pytest_html import extras
                    report.extra = [extras.{extra_type}('{content}')]
        """
        )
        testdir.makepyfile("def test_pass(): pass")
        result, html = run(testdir)
        assert result.ret == 0
        src = f"assets/test_extra_image_separated.py__test_pass_0_0.{file_extension}"
        link = f'<a class="image" href="{src}" target="_blank">'
        assert link in html
        assert os.path.exists(src)

    @pytest.mark.parametrize(
        "file_extension, extra_type",
        [("png", "image"), ("png", "png"), ("svg", "svg"), ("jpg", "jpg")],
    )
    def test_extra_image_separated_rerun(self, testdir, file_extension, extra_type):
        content = b64encode(b"foo").decode("ascii")
        testdir.makeconftest(
            f"""
            import pytest
            @pytest.hookimpl(hookwrapper=True)
            def pytest_runtest_makereport(item, call):
                outcome = yield
                report = outcome.get_result()
                if report.when == 'call':
                    from pytest_html import extras
                    report.extra = [extras.{extra_type}('{content}')]
        """
        )
        testdir.makepyfile(
            """
            import pytest
            @pytest.mark.flaky(reruns=2)
            def test_fail():
                assert False"""
        )
        result, html = run(testdir)

        for i in range(1, 4):
            asset_name = "test_extra_image_separated_rerun.py__test_fail"
            src = f"assets/{asset_name}_0_{i}.{file_extension}"
            link = f'<a class="image" href="{src}" target="_blank">'
            assert result.ret
            assert link in html
            assert os.path.exists(src)

    @pytest.mark.parametrize("src_type", ["https://", "file://", "image.png"])
    def test_extra_image_non_b64(self, testdir, src_type):
        content = src_type
        testdir.makeconftest(
            f"""
            import pytest
            @pytest.hookimpl(hookwrapper=True)
            def pytest_runtest_makereport(item, call):
                outcome = yield
                report = outcome.get_result()
                if report.when == 'call':
                    from pytest_html import extras
                    report.extra = [extras.image('{content}')]
        """
        )
        testdir.makepyfile("def test_pass(): pass")
        if src_type == "image.png":
            testdir.makefile(".png", image="pretty picture")
        result, html = run(testdir, "report.html")
        assert result.ret == 0
        assert '<a href="{0}"><img src="{0}"/>'.format(content) in html

    def test_very_long_test_name(self, testdir):
        testdir.makeconftest(
            """
            import pytest
            @pytest.hookimpl(hookwrapper=True)
            def pytest_runtest_makereport(item, call):
                outcome = yield
                report = outcome.get_result()
                if report.when == 'call':
                    from pytest_html import extras
                    report.extra = [extras.image('image.png')]
        """
        )
        # This will get truncated
        test_name = "test_{}".format("a" * 300)
        testdir.makepyfile(
            f"""
            def {test_name}():
                assert False
        """
        )
        result, html = run(testdir)
        file_name = f"test_very_long_test_name.py__{test_name}_0_0.png"[-255:]
        src = "assets/" + file_name
        link = f'<a class="image" href="{src}" target="_blank">'
        assert result.ret
        assert link in html
        assert os.path.exists(src)

    def test_no_invalid_characters_in_filename(self, testdir):
        testdir.makeconftest(
            """
            import pytest
            @pytest.hookimpl(hookwrapper=True)
            def pytest_runtest_makereport(item, call):
                outcome = yield
                report = outcome.get_result()
                if report.when == 'call':
                    from pytest_html import extras
                    report.extra = [extras.image('image.png')]
        """
        )
        testdir.makepyfile(
            """
            def test_fail():
                assert False
        """
        )
        run(testdir)
        for filename in os.listdir("assets"):
            assert re.search(r'[:\\<>\*\?\|"}{}~]', filename) is None

    def test_no_environment(self, testdir):
        testdir.makeconftest(
            """
            def pytest_configure(config):
                config._metadata = None
        """
        )
        testdir.makepyfile("def test_pass(): pass")
        result, html = run(testdir)
        assert result.ret == 0
        assert "Environment" not in html

    def test_environment(self, testdir):
        content = str(random.random())
        testdir.makeconftest(
            f"""
            def pytest_configure(config):
                config._metadata['content'] = '{content}'
        """
        )
        testdir.makepyfile("def test_pass(): pass")
        result, html = run(testdir)
        assert result.ret == 0
        assert "Environment" in html
        assert len(re.findall(content, html)) == 1

    def test_environment_xdist(self, testdir):
        content = str(random.random())
        testdir.makeconftest(
            f"""
            def pytest_configure(config):
                for i in range(2):
                    config._metadata['content'] = '{content}'
        """
        )
        testdir.makepyfile("def test_pass(): pass")
        result, html = run(testdir, "report.html", "-n", "1")
        assert result.ret == 0
        assert "Environment" in html
        assert len(re.findall(content, html)) == 1

    def test_environment_xdist_reruns(self, testdir):
        content = str(random.random())
        testdir.makeconftest(
            f"""
            def pytest_configure(config):
                for i in range(2):
                    config._metadata['content'] = '{content}'
        """
        )
        testdir.makepyfile("def test_fail(): assert False")
        result, html = run(testdir, "report.html", "-n", "1", "--reruns", "1")
        assert result.ret
        assert "Environment" in html
        assert len(re.findall(content, html)) == 1

    def test_environment_list_value(self, testdir):
        content = tuple(str(random.random()) for i in range(10))
        content += tuple(random.random() for i in range(10))
        expected_content = ", ".join(str(i) for i in content)
        expected_html_re = fr"<td>content</td>\n\s+<td>{expected_content}</td>"
        testdir.makeconftest(
            f"""
            def pytest_configure(config):
                for i in range(2):
                    config._metadata['content'] = {content}
        """
        )
        testdir.makepyfile("def test_pass(): pass")
        result, html = run(testdir)
        assert result.ret == 0
        assert "Environment" in html
        assert len(re.findall(expected_html_re, html)) == 1

    def test_environment_ordered(self, testdir):
        testdir.makeconftest(
            """
            from collections import OrderedDict
            def pytest_configure(config):
                config._metadata = OrderedDict([('ZZZ', 1), ('AAA', 2)])
        """
        )
        testdir.makepyfile("def test_pass(): pass")
        result, html = run(testdir)
        assert result.ret == 0
        assert "Environment" in html
        assert len(re.findall("ZZZ.+AAA", html, re.DOTALL)) == 1

    def test_xdist_crashing_slave(self, testdir):
        """https://github.com/pytest-dev/pytest-html/issues/21"""
        testdir.makepyfile(
            """
            import os
            def test_exit():
                os._exit(0)
        """
        )
        result, html = run(testdir, "report.html", "-n", "1")
        assert "INTERNALERROR>" not in result.stdout.str()

    def test_utf8_surrogate(self, testdir):
        testdir.makepyfile(
            r"""
            import pytest

            @pytest.mark.parametrize('val', ['\ud800'])
            def test_foo(val):
                pass
        """
        )
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
        pass_content = [
            '<span class="ansi31">RCOLOR',
            '<span class="ansi32">GCOLOR',
            '<span class="ansi33">YCOLOR',
        ]
        testdir.makepyfile(
            r"""
            def test_ansi():
                colors = ['\033[31mRCOLOR\033[0m', '\033[32mGCOLOR\033[0m',
                          '\033[33mYCOLOR\033[0m']
                for color in colors:
                    print(color)
        """
        )
        result, html = run(testdir, "report.html", "--self-contained-html")
        assert result.ret == 0
        for content in pass_content:
            if ANSI:
                assert content in html
            else:
                assert content not in html

    @pytest.mark.parametrize("content", [("'foo'"), ("u'\u0081'")])
    def test_utf8_longrepr(self, testdir, content):
        testdir.makeconftest(
            f"""
            import pytest
            @pytest.hookimpl(hookwrapper=True)
            def pytest_runtest_makereport(item, call):
                outcome = yield
                report = outcome.get_result()
                if report.when == 'call':
                    report.longrepr = 'utf8 longrepr: ' + {content}
        """
        )
        testdir.makepyfile(
            """
            def test_fail():
                testtext = 'utf8 longrepr: '
                assert False
        """
        )
        result, html = run(testdir, "report.html", "--self-contained-html")
        assert result.ret
        assert "utf8 longrepr" in html

    def test_collect_error(self, testdir):
        testdir.makepyfile(
            """
            import xyz
            def test_pass(): pass
        """
        )
        result, html = run(testdir)
        assert result.ret
        assert_results(html, tests=0, passed=0, errors=1)
        regex_error = "(Import|ModuleNotFound)Error: No module named .*xyz"
        assert re.search(regex_error, html) is not None

    @pytest.mark.parametrize("colors", [(["red"]), (["green", "blue"])])
    def test_css(self, testdir, recwarn, colors):
        testdir.makepyfile("def test_pass(): pass")
        css = {}
        cssargs = []
        for color in colors:
            style = f"* {{color: {color}}}"
            path = testdir.makefile(".css", **{color: style})
            css[color] = {"style": style, "path": path}
            cssargs.extend(["--css", path])
        result, html = run(testdir, "report.html", "--self-contained-html", *cssargs)
        assert result.ret == 0
        assert len(recwarn) == 0
        for k, v in css.items():
            assert str(v["path"]) in html
            assert v["style"] in html

    def test_css_invalid(self, testdir, recwarn):
        testdir.makepyfile("def test_pass(): pass")
        result = testdir.runpytest("--html", "report.html", "--css", "style.css")
        assert result.ret
        assert len(recwarn) == 0
        assert "No such file or directory: 'style.css'" in result.stderr.str()

    def test_css_invalid_no_html(self, testdir):
        testdir.makepyfile("def test_pass(): pass")
        result = testdir.runpytest("--css", "style.css")
        assert result.ret == 0
        
    def test_report_display_utf8(self, testdir):
        testdir.makepyfile(
            """
            import pytest
            @pytest.mark.parametrize("caseName,input,expected", [('测试用例名称', '6*6', 36)])
            def test_eval(caseName, input, expected):
                assert eval(input) == expected
        """
        )
        result, html = run(testdir)
        assert result.ret == 0
        assert r'\u6d4b\u8bd5\u7528\u4f8b\u540d\u79f0' not in html
