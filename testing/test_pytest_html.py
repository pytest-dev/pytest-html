# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import builtins
import json
import os
import random
import re
from base64 import b64encode

import pkg_resources
import pytest

pytest_plugins = ("pytester",)

if os.name == "nt":
    # Force a utf-8 encoding on file io (since by default windows does not). See
    # https://github.com/pytest-dev/pytest-html/issues/336
    #  If we drop support for Python 3.6 and earlier could use python -X utf8 instead.
    _real_open = builtins.open

    def _open(file, mode="r", buffering=-1, encoding=None, *args, **kwargs):
        if mode in ("r", "w") and encoding is None:
            encoding = "utf-8"

        return _real_open(file, mode, buffering, encoding, *args, **kwargs)

    builtins.open = _open


def remove_deprecation_from_recwarn(recwarn):
    # TODO: Temporary hack until they fix
    # https://github.com/pytest-dev/pytest/issues/6936
    return [
        item for item in recwarn if "TerminalReporter.writer" not in repr(item.message)
    ]


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

    @pytest.mark.parametrize(
        "duration_formatter,expected_report_content",
        [
            ("%f", r'<td class="col-duration">\d{2}</td>'),
            ("%S.%f", r'<td class="col-duration">\d{2}\.\d{2}</td>'),
            (
                "ABC%H  %M %S123",
                r'<td class="col-duration">ABC\d{2}  \d{2} \d{2}123</td>',
            ),
        ],
    )
    def test_can_format_duration_column(
        self, testdir, duration_formatter, expected_report_content
    ):

        testdir.makeconftest(
            f"""
            import pytest

            @pytest.hookimpl(hookwrapper=True)
            def pytest_runtest_makereport(item, call):
                outcome = yield
                report = outcome.get_result()
                setattr(report, "duration_formatter", "{duration_formatter}")
        """
        )

        sleep = float(0.2)
        testdir.makepyfile(
            """
            import time
            def test_sleep():
                time.sleep({:f})
        """.format(
                sleep
            )
        )
        result, html = run(testdir)
        assert result.ret == 0
        assert_results(html, duration=sleep)

        compiled_regex = re.compile(expected_report_content)
        assert compiled_regex.search(html)

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

    @pytest.mark.flaky(reruns=2)  # test is flaky on windows
    def test_rerun(self, testdir):
        testdir.makeconftest(
            """
            import pytest

            @pytest.hookimpl(hookwrapper=True)
            def pytest_runtest_makereport(item, call):
                pytest_html = item.config.pluginmanager.getplugin("html")
                outcome = yield
                report = outcome.get_result()

                extra = getattr(report, "extra", [])
                if report.when == "call":
                    extra.append(pytest_html.extras.url("http://www.example.com/"))
                report.extra = extra
        """
        )

        testdir.makepyfile(
            """
            import pytest
            import time

            @pytest.mark.flaky(reruns=2)
            def test_example():
                time.sleep(1)
                assert False
        """
        )

        result, html = run(testdir)
        assert result.ret
        assert_results(html, passed=0, failed=1, rerun=2)

        expected_report_durations = r'<td class="col-duration">1.\d{2}</td>'
        assert len(re.findall(expected_report_durations, html)) == 3

        expected_report_extras = (
            r'<td class="col-links"><a class="url" href="http://www.example.com/" '
            'target="_blank">URL</a> </td>'
        )
        assert len(re.findall(expected_report_extras, html)) == 3

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

    @pytest.mark.parametrize(
        "path, is_custom", [("", False), ("", True), ("directory", False)]
    )
    def test_report_title(self, testdir, path, is_custom):
        testdir.makepyfile("def test_pass(): pass")

        report_name = "report.html"
        report_title = "My Custom Report" if is_custom else report_name
        if is_custom:
            testdir.makeconftest(
                f"""
                import pytest
                from py.xml import html

                def pytest_html_report_title(report):
                    report.title = "{report_title}"
            """
            )

        path = os.path.join(path, report_name)
        result, html = run(testdir, path)
        assert result.ret == 0

        report_head_title_string = f"<title>{report_title}</title>"
        assert len(re.findall(report_head_title_string, html)) == 1, html

        report_body_title_string = f"<h1>{report_title}</h1>"
        assert len(re.findall(report_body_title_string, html)) == 1, html

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
        mock_isfile = mocker.patch("pytest_html.result.isfile")
        mock_isfile.side_effect = ValueError("stat: path too long for Windows")
        self.test_extra_image(testdir, "image/png", "png")
        assert mock_isfile.call_count == 1

    @pytest.mark.parametrize("mime_type, extension", [("video/mp4", "mp4")])
    def test_extra_video(self, testdir, mime_type, extension):
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
        assert (
            f'<video controls><source src="{src}" type="{mime_type}"></video>' in html
        )

    def test_extra_video_windows(self, mocker, testdir):
        mock_isfile = mocker.patch("pytest_html.result.isfile")
        mock_isfile.side_effect = ValueError("stat: path too long for Windows")
        self.test_extra_video(testdir, "video/mp4", "mp4")
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
        img = f'<img src="{src}"/>'
        assert link in html
        assert img in html
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
            img = f'<img src="{src}"/>'
            assert result.ret
            assert link in html
            assert img in html
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

    @pytest.mark.parametrize("max_asset_filename_length", [10, 100])
    def test_very_long_test_name(self, testdir, max_asset_filename_length):
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
        testdir.makeini(
            f"""
            [pytest]
            max_asset_filename_length = {max_asset_filename_length}
        """
        )
        result, html = run(testdir, "report.html")
        file_name = f"test_very_long_test_name.py__{test_name}_0_0.png"[
            -max_asset_filename_length:
        ]
        src = "assets/" + file_name
        link = f'<a class="image" href="{src}" target="_blank">'
        img = f'<img src="{src}"/>'
        assert result.ret
        assert link in html
        assert img in html
        assert os.path.exists(src)

    def test_extra_fixture(self, testdir):
        content = b64encode(b"foo").decode("ascii")
        testdir.makepyfile(
            f"""
            def test_pass(extra):
                from pytest_html import extras
                extra.append(extras.png('{content}'))
        """
        )
        result, html = run(testdir, "report.html", "--self-contained-html")
        assert result.ret == 0
        src = f"data:image/png;base64,{content}"
        assert f'<img src="{src}"/>' in html

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

    _unsorted_tuples = [
        ("Hello", "fzWZP6vKRv", "hello", "garAge", "123Go"),
        (2, 4, 2, 1, 54),
        ("Yes", 400, "5.4"),
    ]
    _sorted_tuples = [
        "123Go, Hello, fzWZP6vKRv, garAge, hello",
        "1, 2, 2, 4, 54",
        "400, 5.4, Yes",
    ]
    _test_environment_list_value_data_set = zip(_unsorted_tuples, _sorted_tuples)

    @pytest.mark.parametrize(
        "content,expected_content", _test_environment_list_value_data_set
    )
    def test_environment_list_value(self, testdir, content, expected_content):
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

    _unordered_dict = {k: len(k) for k in _unsorted_tuples[0]}
    _unordered_dict_expected = (
        r'<td>content</td>\n\s+<td>{"123Go": 5, "Hello": 5, '
        r'"fzWZP6vKRv": 10, "garAge": 6, "hello": 5}</td>'
    )
    _unordered_dict_with_html = {
        "First Link": r'<a href="https://www.w3schools.com">W3Schools</a>',
        "Second Link": r'<a href="https://www.w3schools.com">W2Schools</a>',
        "Third Link": r'<a href="https://www.w3schools.com">W4Schools</a>',
    }
    _unordered_dict_with_html_expected = (
        r"<td>content</td>\n\s+<td>{"
        r'"First Link": "<a href=\\"https://www.w3schools.com\\">W3Schools</a>", '
        r'"Second Link": "<a href=\\"https://www.w3schools.com\\">W2Schools</a>", '
        r'"Third Link": "<a href=\\"https://www.w3schools.com\\">W4Schools</a>"}</td>'
    )

    @pytest.mark.parametrize(
        "unordered_dict,expected_output",
        [
            (_unordered_dict, _unordered_dict_expected),
            (_unordered_dict_with_html, _unordered_dict_with_html_expected),
        ],
    )
    def test_environment_unordered_dict_value(
        self, testdir, unordered_dict, expected_output
    ):
        testdir.makeconftest(
            f"""
            def pytest_configure(config):
                values = dict({json.dumps(unordered_dict)})
                config._metadata['content'] = values
        """
        )
        testdir.makepyfile("def test_pass(): pass")
        result, html = run(testdir)
        assert result.ret == 0
        assert "Environment" in html
        assert len(re.findall(expected_output, html)) == 1

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

    def test_xdist_crashing_worker(self, testdir):
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

    @pytest.mark.parametrize(
        "with_ansi",
        [True, False],
    )
    def test_ansi_color(self, testdir, mocker, with_ansi):
        if not with_ansi:
            mock_ansi_support = mocker.patch("pytest_html.html_report.ansi_support")
            mock_ansi_support = mocker.patch("pytest_html.result.ansi_support")
            mock_ansi_support.return_value = None

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
            if with_ansi:
                assert content in html
            else:
                assert content not in html

    def test_ansi_escape_sequence_removed(self, testdir):
        testdir.makeini(
            r"""
            [pytest]
            log_cli = 1
            log_cli_level = INFO
        """
        )
        testdir.makepyfile(
            r"""
            import logging
            logging.basicConfig()
            LOGGER = logging.getLogger()
            def test_ansi():
                LOGGER.info("ANSI removed")
        """
        )
        result, html = run(
            testdir, "report.html", "--self-contained-html", "--color=yes"
        )
        assert result.ret == 0
        assert not re.search(r"\[[\d;]+m", html)

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
        warnings = remove_deprecation_from_recwarn(recwarn)
        assert len(warnings) == 0
        for k, v in css.items():
            assert str(v["path"]) in html
            assert v["style"] in html

    @pytest.mark.parametrize(
        "files",
        [
            "style.css",
            ["abc.css", "xyz.css"],
            "testdir.makefile('.css', * {color: 'white'}",
        ],
    )
    def test_css_invalid(self, testdir, recwarn, files):
        testdir.makepyfile("def test_pass(): pass")
        path = files
        if isinstance(files, list):
            file1 = files[0]
            file2 = files[1]
            result = testdir.runpytest(
                "--html", "report.html", "--css", file1, "--css", file2
            )
        else:
            result = testdir.runpytest("--html", "report.html", "--css", path)
        assert result.ret
        assert len(recwarn) == 0
        if isinstance(files, list):
            assert files[0] in result.stderr.str() and files[1] in result.stderr.str()
        else:
            assert path in result.stderr.str()

    def test_css_invalid_no_html(self, testdir):
        testdir.makepyfile("def test_pass(): pass")
        result = testdir.runpytest("--css", "style.css")
        assert result.ret == 0

    def test_report_display_utf8(self, testdir):
        testdir.makepyfile(
            """
            import pytest
            @pytest.mark.parametrize("utf8", [("测试用例名称")])
            def test_pass(utf8):
                assert True
        """
        )
        result, html = run(testdir)
        assert result.ret == 0
        assert r"\u6d4b\u8bd5\u7528\u4f8b\u540d\u79f0" not in html

    @pytest.mark.parametrize("is_collapsed", [True, False])
    def test_collapsed(self, testdir, is_collapsed):
        collapsed_html = '<tr class="collapsed">'
        expected_count = 2 if is_collapsed else 0
        testdir.makeini(
            f"""
            [pytest]
            render_collapsed = {is_collapsed}
        """
        )
        testdir.makepyfile(
            """
            def test_fail():
                assert False

            def test_pass():
                assert True
        """
        )
        result, html = run(testdir)
        assert result.ret == 1
        assert len(re.findall(collapsed_html, html)) == expected_count
        assert_results(html, tests=2, passed=1, failed=1)

    def test_setup_and_teardown_in_html(self, testdir):
        testdir.makepyfile(
            """
            import pytest
            @pytest.fixture(scope="function")
            def setupAndTeardown():
                print ("this is setup")
                yield
                print ("this is teardown")

            def test_setup_and_teardown(setupAndTeardown):
                print ("this is the test case")
        """
        )
        result, html = run(testdir)
        assert result.ret == 0
        assert_results(html, tests=1, passed=1)
        assert "this is setup" in html
        assert "this is teardown" in html
        assert "this is the test case" in html

    def test_setup_failures_are_errors(self, testdir):
        testdir.makepyfile(
            """
            import pytest
            @pytest.fixture(scope="function")
            def setup():
                assert 0, "failure!"

            def test_setup(setup):
                print ("this is the test case")
        """
        )
        result, html = run(testdir)
        assert result.ret == 1
        assert_results(html, tests=0, passed=0, errors=1)
        assert "this is the test case" not in html

    def test_teardown_failures_are_errors(self, testdir):
        testdir.makepyfile(
            """
            import pytest
            @pytest.fixture(scope="function")
            def teardown():
                yield
                assert 0, "failure!"

            def test_setup(teardown):
                print ("this is the test case")
        """
        )
        result, html = run(testdir)
        assert result.ret == 1
        assert_results(html, tests=0, passed=0, errors=1)
        assert "this is the test case" in html

    @pytest.mark.parametrize(
        "capture_flag, should_capture",
        [("-s", False), ("--capture=no", False), ("--capture=sys", True)],
    )
    def test_extra_log_reporting_respects_capture_no(
        self, testdir, capture_flag, should_capture
    ):
        testdir.makepyfile(
            """
            import sys
            def test_capture_no():
                print("stdout print line")
                print("stderr print line", file=sys.stderr)
        """
        )

        result, html = run(testdir, "report.html", capture_flag)
        assert result.ret == 0
        assert_results(html)

        extra_log_div_regex = re.compile(
            '<div class="log"> -+Captured stdout call-+ <br/>stdout print line\n<br/> '
            "-+Captured stderr call-+ <br/>stderr print line\n<br/></div>"
        )
        if should_capture:
            assert extra_log_div_regex.search(html) is not None
        else:
            assert extra_log_div_regex.search(html) is None

    @pytest.mark.parametrize(
        "show_capture_flag, should_capture",
        [("--show-capture=no", False), ("--show-capture=all", True)],
    )
    def test_extra_log_reporting_respects_show_capture_no(
        self, testdir, show_capture_flag, should_capture
    ):
        testdir.makepyfile(
            """
            import sys
            def test_show_capture_no():
                print("stdout print line")
                print("stderr print line", file=sys.stderr)
                assert False
        """
        )

        result, html = run(testdir, "report.html", show_capture_flag)
        assert result.ret == 1
        assert_results(html, passed=0, failed=1)

        extra_log_div_regex = re.compile(
            '<div class="log">.*-+Captured stdout call-+ <br/>stdout print line\n<br/> '
            "-+Captured stderr call-+ <br/>stderr print line\n<br/></div>"
        )
        if should_capture:
            assert extra_log_div_regex.search(html) is not None
        else:
            assert extra_log_div_regex.search(html) is None

    def test_environment_table_redact_list(self, testdir):
        testdir.makeini(
            """
            [pytest]
            environment_table_redact_list = ^foo$
                .*redact.*
                bar
        """
        )

        testdir.makeconftest(
            """
            def pytest_configure(config):
                config._metadata["foo"] = "will not appear a"
                config._metadata["afoo"] = "will appear"
                config._metadata["foos"] = "will appear"
                config._metadata["redact"] = "will not appear ab"
                config._metadata["will_redact"] = "will not appear abc"
                config._metadata["redacted_item"] = "will not appear abcd"
                config._metadata["unrelated_item"] = "will appear"
                config._metadata["bar"] = "will not appear abcde"
                config._metadata["bars"] = "will not appear abcdef"
        """
        )

        testdir.makepyfile(
            """
            def test_pass():
                assert True
        """
        )

        result, html = run(testdir)
        assert result.ret == 0
        assert_results(html)

        black_box_ascii_value = 0x2593
        expected_environment_values = {
            "foo": "".join(chr(black_box_ascii_value) for value in range(17)),
            "afoo": "will appear",
            "foos": "will appear",
            "redact": "".join(chr(black_box_ascii_value) for value in range(18)),
            "will_redact": "".join(chr(black_box_ascii_value) for value in range(19)),
            "redacted_item": "".join(chr(black_box_ascii_value) for value in range(20)),
            "unrelated_item": "will appear",
            "bar": "".join(chr(black_box_ascii_value) for value in range(21)),
            "bars": "".join(chr(black_box_ascii_value) for value in range(22)),
        }
        for variable in expected_environment_values:
            variable_value = expected_environment_values[variable]
            variable_value_regex = re.compile(
                f"<tr>\n.*<td>{variable}</td>\n.*<td>{variable_value}</td></tr>"
            )
            assert variable_value_regex.search(html) is not None
