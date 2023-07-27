import base64
import importlib.resources
import json
import os
import random
import re
import urllib.parse
from base64 import b64encode
from pathlib import Path

import pytest
from assertpy import assert_that
from bs4 import BeautifulSoup
from selenium import webdriver

pytest_plugins = ("pytester",)

OUTCOMES = {
    "passed": "Passed",
    "skipped": "Skipped",
    "failed": "Failed",
    "error": "Errors",
    "xfailed": "Unexpected failures",
    "xpassed": "Unexpected passes",
    "rerun": "Reruns",
}


def run(pytester, path="report.html", cmd_flags=None, query_params=None):
    cmd_flags = cmd_flags or []
    query_params = urllib.parse.urlencode(query_params) if query_params else {}

    path = pytester.path.joinpath(path)
    pytester.runpytest("--html", path, *cmd_flags)

    chrome_options = webdriver.ChromeOptions()
    if os.environ.get("CI", False):
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920x1080")
    driver = webdriver.Remote(
        command_executor="http://127.0.0.1:4444", options=chrome_options
    )
    try:
        # Begin workaround
        # See: https://github.com/pytest-dev/pytest/issues/10738
        path.chmod(0o755)
        for parent in path.parents:
            try:
                os.chmod(parent, 0o755)
            except PermissionError:
                continue
        # End workaround

        driver.get(f"file:///reports{path}?{query_params}")
        return BeautifulSoup(driver.page_source, "html.parser")
    finally:
        driver.quit()


def assert_results(
    page,
    passed=0,
    skipped=0,
    failed=0,
    error=0,
    xfailed=0,
    xpassed=0,
    rerun=0,
    total_tests=None,
):
    args = locals()
    number_of_tests = 0
    for outcome, number in args.items():
        if outcome == "total_tests":
            continue
        if isinstance(number, int):
            number_of_tests += number
            result = get_text(page, f"span[class={outcome}]")
            assert_that(result).matches(rf"{number} {OUTCOMES[outcome]}")


def get_element(page, selector):
    return page.select_one(selector)


def get_text(page, selector):
    return get_element(page, selector).string


def is_collapsed(page, test_name):
    return get_element(page, f".summary tbody[id$='{test_name}'] .collapsed")


def get_log(page, test_id=None):
    # TODO(jim) move to get_text (use .contents)
    if test_id:
        log = get_element(page, f".summary tbody[id$='{test_id}'] div[class='log']")
    else:
        log = get_element(page, ".summary div[class='log']")
    all_text = ""
    for text in log.strings:
        all_text += text

    return all_text


def file_content():
    try:
        return (
            importlib.resources.files("pytest_html")
            .joinpath("resources", "style.css")
            .read_bytes()
            .decode("utf-8")
            .strip()
        )
    except AttributeError:
        # Needed for python < 3.9
        import pkg_resources

        return pkg_resources.resource_string(
            "pytest_html", os.path.join("resources", "style.css")
        ).decode("utf-8")


class TestHTML:
    @pytest.mark.parametrize(
        "pause, expectation",
        [
            (0.4, 400),
            (1, r"^((?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d$)"),
        ],
    )
    def test_durations(self, pytester, pause, expectation):
        pytester.makepyfile(
            f"""
            import time
            def test_sleep():
                time.sleep({pause})
        """
        )
        page = run(pytester)
        duration = get_text(page, "#results-table td[class='col-duration']")
        total_duration = get_text(page, "p[class='run-count']")
        if pause < 1:
            assert_that(int(duration.replace("ms", ""))).is_between(
                expectation, expectation * 2
            )
            assert_that(total_duration).matches(r"\d+\s+ms")
        else:
            assert_that(duration).matches(expectation)
            assert_that(total_duration).matches(r"\d{2}:\d{2}:\d{2}")

    def test_total_number_of_tests_zero(self, pytester):
        page = run(pytester)
        assert_results(page)

        total = get_text(page, "p[class='run-count']")
        assert_that(total).matches(r"0 test(?!s)")

    def test_total_number_of_tests_singular(self, pytester):
        pytester.makepyfile("def test_pass(): pass")
        page = run(pytester)
        assert_results(page, passed=1)

        total = get_text(page, "p[class='run-count']")
        assert_that(total).matches(r"1 test(?!s)")

    def test_total_number_of_tests_plural(self, pytester):
        pytester.makepyfile(
            """
            def test_pass_one(): pass
            def test_pass_two(): pass
            """
        )
        page = run(pytester)
        assert_results(page, passed=2)

        total = get_text(page, "p[class='run-count']")
        assert_that(total).matches(r"2 tests(?!\S)")

    def test_pass(self, pytester):
        pytester.makepyfile("def test_pass(): pass")
        page = run(pytester)
        assert_results(page, passed=1)

    def test_skip(self, pytester):
        reason = str(random.random())
        pytester.makepyfile(
            f"""
            import pytest
            def test_skip():
                pytest.skip("{reason}")
        """
        )
        page = run(pytester)
        assert_results(page, skipped=1, total_tests=0)

        log = get_text(page, ".summary div[class='log']")
        assert_that(log).contains(reason)

    def test_skip_function_marker(self, pytester):
        reason = str(random.random())
        pytester.makepyfile(
            f"""
            import pytest
            @pytest.mark.skip(reason="{reason}")
            def test_skip():
                assert True
        """
        )
        page = run(pytester)
        assert_results(page, skipped=1, total_tests=0)

        log = get_text(page, ".summary div[class='log']")
        assert_that(log).contains(reason)

    def test_skip_class_marker(self, pytester):
        reason = str(random.random())
        pytester.makepyfile(
            f"""
            import pytest
            @pytest.mark.skip(reason="{reason}")
            class TestSkip:
                def test_skip():
                    assert True
        """
        )
        page = run(pytester)
        assert_results(page, skipped=1, total_tests=0)

        log = get_text(page, ".summary div[class='log']")
        assert_that(log).contains(reason)

    def test_fail(self, pytester):
        pytester.makepyfile("def test_fail(): assert False")
        page = run(pytester)
        assert_results(page, failed=1)
        assert_that(get_log(page)).contains("AssertionError")
        assert_that(get_text(page, ".summary div[class='log'] span.error")).matches(
            r"^E\s+assert False$"
        )

    def test_xfail(self, pytester):
        reason = str(random.random())
        pytester.makepyfile(
            f"""
            import pytest
            def test_xfail():
                pytest.xfail("{reason}")
        """
        )
        page = run(pytester)
        assert_results(page, xfailed=1)
        assert_that(get_log(page)).contains(reason)

    def test_xfail_function_marker(self, pytester):
        reason = str(random.random())
        pytester.makepyfile(
            f"""
            import pytest
            @pytest.mark.xfail(reason="{reason}")
            def test_xfail():
                assert False
        """
        )
        page = run(pytester)
        assert_results(page, xfailed=1)
        assert_that(get_log(page)).contains(reason)

    def test_xfail_class_marker(self, pytester):
        pytester.makepyfile(
            """
            import pytest
            @pytest.mark.xfail(reason="broken")
            class TestXFail:
                def test_xfail(self):
                    assert False
        """
        )
        page = run(pytester)
        assert_results(page, xfailed=1)

    def test_xpass(self, pytester):
        pytester.makepyfile(
            """
            import pytest
            @pytest.mark.xfail()
            def test_xpass():
                assert True
        """
        )
        page = run(pytester)
        assert_results(page, xpassed=1)

    def test_xpass_class_marker(self, pytester):
        pytester.makepyfile(
            """
            import pytest
            @pytest.mark.xfail()
            class TestXPass:
                def test_xpass(self):
                    assert True
        """
        )
        page = run(pytester)
        assert_results(page, xpassed=1)

    def test_rerun(self, pytester):
        pytester.makepyfile(
            """
            import pytest
            import time

            @pytest.mark.flaky(reruns=2)
            def test_example():
                time.sleep(0.2)
                assert False
        """
        )

        page = run(pytester)
        assert_results(page, failed=1, rerun=2, total_tests=1)

    def test_conditional_xfails(self, pytester):
        pytester.makepyfile(
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
        page = run(pytester)
        assert_results(page, passed=1, failed=1, xfailed=1, xpassed=1)

    def test_setup_error(self, pytester):
        pytester.makepyfile(
            """
            import pytest
            @pytest.fixture
            def arg(request):
                raise ValueError()
            def test_function(arg):
                pass
        """
        )
        page = run(pytester)
        assert_results(page, error=1, total_tests=0)

        col_name = get_text(page, ".summary td[class='col-name']")
        assert_that(col_name).contains("::setup")
        assert_that(get_log(page)).contains("ValueError")

    @pytest.mark.parametrize("title", ["", "Special Report"])
    def test_report_title(self, pytester, title):
        pytester.makepyfile("def test_pass(): pass")

        if title:
            pytester.makeconftest(
                f"""
                import pytest
                def pytest_html_report_title(report):
                    report.title = "{title}"
            """
            )

        expected_title = title if title else "report.html"
        page = run(pytester)
        assert_that(get_text(page, "#head-title")).is_equal_to(expected_title)
        assert_that(get_text(page, "h1[id='title']")).is_equal_to(expected_title)

    def test_resources_inline_css(self, pytester):
        pytester.makepyfile("def test_pass(): pass")
        page = run(pytester, cmd_flags=["--self-contained-html"])

        content = file_content()

        assert_that(get_text(page, "head style").strip()).contains(content)

    def test_resources_css(self, pytester):
        pytester.makepyfile("def test_pass(): pass")
        page = run(pytester)

        assert_that(page.select_one("head link")["href"]).is_equal_to(
            str(Path("assets", "style.css"))
        )

    def test_custom_content_in_summary(self, pytester):
        content = {
            "prefix": str(random.random()),
            "summary": str(random.random()),
            "postfix": str(random.random()),
        }

        pytester.makeconftest(
            f"""
            import pytest

            def pytest_html_results_summary(prefix, summary, postfix):
                prefix.append(r"<p>prefix is {content['prefix']}</p>")
                summary.extend([r"<p>summary is {content['summary']}</p>"])
                postfix.extend([r"<p>postfix is {content['postfix']}</p>"])
        """
        )

        pytester.makepyfile("def test_pass(): pass")
        page = run(pytester)

        elements = page.select(".summary__data p:not(.run-count):not(.filter)")
        assert_that(elements).is_length(3)
        for element in elements:
            key = re.search(r"(\w+).*", element.string).group(1)
            value = content.pop(key)
            assert_that(element.string).contains(value)

    def test_extra_html(self, pytester):
        content = str(random.random())
        pytester.makeconftest(
            f"""
            import pytest

            @pytest.hookimpl(hookwrapper=True)
            def pytest_runtest_makereport(item, call):
                outcome = yield
                report = outcome.get_result()
                if report.when == 'call':
                    from pytest_html import extras
                    report.extras = [extras.html('<div>{content}</div>')]
        """
        )

        pytester.makepyfile("def test_pass(): pass")
        page = run(pytester)

        assert_that(page.select_one(".summary .extraHTML").string).is_equal_to(content)

    @pytest.mark.parametrize(
        "content, encoded",
        [("u'\u0081'", "woE="), ("'foo'", "Zm9v"), ("b'\\xe2\\x80\\x93'", "4oCT")],
    )
    def test_extra_text(self, pytester, content, encoded):
        pytester.makeconftest(
            f"""
            import pytest
            @pytest.hookimpl(hookwrapper=True)
            def pytest_runtest_makereport(item, call):
                outcome = yield
                report = outcome.get_result()
                if report.when == 'call':
                    from pytest_html import extras
                    report.extras = [extras.text({content})]
        """
        )

        pytester.makepyfile("def test_pass(): pass")
        page = run(pytester, cmd_flags=["--self-contained-html"])

        element = page.select_one(".summary a[class='col-links__extra text']")
        assert_that(element.string).is_equal_to("Text")
        assert_that(element["href"]).is_equal_to(
            f"data:text/plain;charset=utf-8;base64,{encoded}"
        )

    def test_extra_json(self, pytester):
        content = {str(random.random()): str(random.random())}
        pytester.makeconftest(
            f"""
            import pytest

            @pytest.hookimpl(hookwrapper=True)
            def pytest_runtest_makereport(item, call):
                outcome = yield
                report = outcome.get_result()
                if report.when == 'call':
                    from pytest_html import extras
                    report.extras = [extras.json({content})]
        """
        )

        pytester.makepyfile("def test_pass(): pass")
        page = run(pytester, cmd_flags=["--self-contained-html"])

        content_str = json.dumps(content)
        data = b64encode(content_str.encode("utf-8")).decode("ascii")

        element = page.select_one(".summary a[class='col-links__extra json']")
        assert_that(element.string).is_equal_to("JSON")
        assert_that(element["href"]).is_equal_to(
            f"data:application/json;charset=utf-8;base64,{data}"
        )

    def test_extra_url(self, pytester):
        content = str(random.random())
        pytester.makeconftest(
            f"""
            import pytest

            @pytest.hookimpl(hookwrapper=True)
            def pytest_runtest_makereport(item, call):
                outcome = yield
                report = outcome.get_result()
                if report.when == 'call':
                    from pytest_html import extras
                    report.extras = [extras.url('{content}')]
        """
        )
        pytester.makepyfile("def test_pass(): pass")
        page = run(pytester)

        element = page.select_one(".summary a[class='col-links__extra url']")
        assert_that(element.string).is_equal_to("URL")
        assert_that(element["href"]).is_equal_to(content)

    @pytest.mark.parametrize(
        "mime_type, extension",
        [
            ("image/png", "png"),
            ("image/png", "image"),
            ("image/jpeg", "jpg"),
            ("image/svg+xml", "svg"),
        ],
    )
    def test_extra_image(self, pytester, mime_type, extension):
        content = str(random.random())
        charset = "utf-8"
        data = base64.b64encode(content.encode(charset)).decode(charset)

        pytester.makeconftest(
            f"""
            import pytest

            @pytest.hookimpl(hookwrapper=True)
            def pytest_runtest_makereport(item, call):
                outcome = yield
                report = outcome.get_result()
                if report.when == 'call':
                    from pytest_html import extras
                    report.extras = [extras.{extension}('{data}')]
        """
        )
        pytester.makepyfile("def test_pass(): pass")
        page = run(pytester, cmd_flags=["--self-contained-html"])

        # element = page.select_one(".summary a[class='col-links__extra image']")
        src = f"data:{mime_type};base64,{data}"
        # assert_that(element.string).is_equal_to("Image")
        # assert_that(element["href"]).is_equal_to(src)

        element = page.select_one(".summary .media img")
        assert_that(str(element)).is_equal_to(f'<img src="{src}"/>')

    @pytest.mark.parametrize("mime_type, extension", [("video/mp4", "mp4")])
    def test_extra_video(self, pytester, mime_type, extension):
        content = str(random.random())
        charset = "utf-8"
        data = base64.b64encode(content.encode(charset)).decode(charset)
        pytester.makeconftest(
            f"""
            import pytest
            @pytest.hookimpl(hookwrapper=True)
            def pytest_runtest_makereport(item, call):
                outcome = yield
                report = outcome.get_result()
                if report.when == 'call':
                    from pytest_html import extras
                    report.extras = [extras.{extension}('{data}')]
        """
        )
        pytester.makepyfile("def test_pass(): pass")
        page = run(pytester, cmd_flags=["--self-contained-html"])

        # element = page.select_one(".summary a[class='col-links__extra video']")
        src = f"data:{mime_type};base64,{data}"
        # assert_that(element.string).is_equal_to("Video")
        # assert_that(element["href"]).is_equal_to(src)

        element = page.select_one(".summary .media video")
        assert_that(str(element)).is_equal_to(
            f'<video controls="">\n<source src="{src}" type="{mime_type}"/>\n</video>'
        )

    def test_xdist(self, pytester):
        pytester.makepyfile("def test_xdist(): pass")
        page = run(pytester, cmd_flags=["-n1"])
        assert_results(page, passed=1)

    def test_results_table_hook_append(self, pytester):
        header_selector = (
            ".summary #results-table-head tr:nth-child(1) th:nth-child({})"
        )
        row_selector = ".summary #results-table tr:nth-child(1) td:nth-child({})"

        pytester.makeconftest(
            """
            def pytest_html_results_table_header(cells):
                cells.append("<th>Description</th>")
                cells.append(
                    '<th class="sortable time" data-column-type="time">Time</th>'
                )

            def pytest_html_results_table_row(report, cells):
                cells.append("<td>A description</td>")
                cells.append('<td class="col-time">A time</td>')
        """
        )
        pytester.makepyfile("def test_pass(): pass")
        page = run(pytester)

        description_index = 5
        time_index = 6
        assert_that(get_text(page, header_selector.format(time_index))).is_equal_to(
            "Time"
        )
        assert_that(
            get_text(page, header_selector.format(description_index))
        ).is_equal_to("Description")

        assert_that(get_text(page, row_selector.format(time_index))).is_equal_to(
            "A time"
        )
        assert_that(get_text(page, row_selector.format(description_index))).is_equal_to(
            "A description"
        )

    def test_results_table_hook_insert(self, pytester):
        header_selector = (
            ".summary #results-table-head tr:nth-child(1) th:nth-child({})"
        )
        row_selector = ".summary #results-table tr:nth-child(1) td:nth-child({})"

        pytester.makeconftest(
            """
            def pytest_html_results_table_header(cells):
                cells.insert(2, "<th>Description</th>")
                cells.insert(
                    1,
                    '<th class="sortable time" data-column-type="time">Time</th>'
                )

            def pytest_html_results_table_row(report, cells):
                cells.insert(2, "<td>A description</td>")
                cells.insert(1, '<td class="col-time">A time</td>')
        """
        )
        pytester.makepyfile("def test_pass(): pass")
        page = run(pytester)

        description_index = 4
        time_index = 2
        assert_that(get_text(page, header_selector.format(time_index))).is_equal_to(
            "Time"
        )
        assert_that(
            get_text(page, header_selector.format(description_index))
        ).is_equal_to("Description")

        assert_that(get_text(page, row_selector.format(time_index))).is_equal_to(
            "A time"
        )
        assert_that(get_text(page, row_selector.format(description_index))).is_equal_to(
            "A description"
        )

    def test_results_table_hook_delete(self, pytester):
        pytester.makeconftest(
            """
            def pytest_html_results_table_row(report, cells):
                if report.skipped:
                    del cells[:]
        """
        )
        pytester.makepyfile(
            """
            import pytest
            def test_skip():
                pytest.skip('reason')

            def test_pass(): pass

        """
        )
        page = run(pytester)
        assert_results(page, passed=1)

    def test_results_table_hook_pop(self, pytester):
        pytester.makeconftest(
            """
            def pytest_html_results_table_header(cells):
                cells.pop()

            def pytest_html_results_table_row(report, cells):
                cells.pop()
        """
        )
        pytester.makepyfile("def test_pass(): pass")
        page = run(pytester)

        header_columns = page.select(".summary #results-table-head th")
        assert_that(header_columns).is_length(3)

        row_columns = page.select_one(".summary .results-table-row").select(
            "td:not(.extra)"
        )
        assert_that(row_columns).is_length(3)

    @pytest.mark.parametrize("no_capture", ["", "-s"])
    def test_standard_streams(self, pytester, no_capture):
        pytester.makepyfile(
            """
            import pytest
            import sys
            @pytest.fixture
            def setup():
                print("this is setup stdout")
                print("this is setup stderr", file=sys.stderr)
                yield
                print("this is teardown stdout")
                print("this is teardown stderr", file=sys.stderr)

            def test_streams(setup):
                print("this is call stdout")
                print("this is call stderr", file=sys.stderr)
                assert True
        """
        )
        page = run(pytester, "report.html", cmd_flags=[no_capture])
        assert_results(page, passed=1)

        log = get_log(page)
        for when in ["setup", "call", "teardown"]:
            for stream in ["stdout", "stderr"]:
                if no_capture:
                    assert_that(log).does_not_match(f"- Captured {stream} {when} -")
                    assert_that(log).does_not_match(f"this is {when} {stream}")
                else:
                    assert_that(log).matches(f"- Captured {stream} {when} -")
                    assert_that(log).matches(f"this is {when} {stream}")


class TestLogCapturing:
    LOG_LINE_REGEX = r"\s+this is {}"

    @pytest.fixture
    def log_cli(self, pytester):
        pytester.makeini(
            """
            [pytest]
            log_cli = 1
            log_cli_level = INFO
            log_cli_date_format = %Y-%m-%d %H:%M:%S
            log_cli_format = %(asctime)s %(levelname)s: %(message)s
        """
        )

    @pytest.fixture
    def test_file(self):
        def formatter(assertion, setup="", teardown="", flaky=""):
            return f"""
                import pytest
                import logging
                @pytest.fixture
                def setup():
                    logging.info("this is setup")
                    {setup}
                    yield
                    logging.info("this is teardown")
                    {teardown}

                {flaky}
                def test_logging(setup):
                    logging.info("this is test")
                    assert {assertion}
            """

        return formatter

    @pytest.mark.usefixtures("log_cli")
    def test_all_pass(self, test_file, pytester):
        pytester.makepyfile(test_file(assertion=True))
        page = run(pytester)
        assert_results(page, passed=1)

        log = get_log(page)
        for when in ["setup", "test", "teardown"]:
            assert_that(log).matches(self.LOG_LINE_REGEX.format(when))

    @pytest.mark.usefixtures("log_cli")
    def test_setup_error(self, test_file, pytester):
        pytester.makepyfile(test_file(assertion=True, setup="error"))
        page = run(pytester)
        assert_results(page, error=1)

        log = get_log(page)
        assert_that(log).matches(self.LOG_LINE_REGEX.format("setup"))
        assert_that(log).does_not_match(self.LOG_LINE_REGEX.format("test"))
        assert_that(log).does_not_match(self.LOG_LINE_REGEX.format("teardown"))

    @pytest.mark.usefixtures("log_cli")
    def test_test_fails(self, test_file, pytester):
        pytester.makepyfile(test_file(assertion=False))
        page = run(pytester)
        assert_results(page, failed=1)

        log = get_log(page)
        for when in ["setup", "test", "teardown"]:
            assert_that(log).matches(self.LOG_LINE_REGEX.format(when))

    @pytest.mark.usefixtures("log_cli")
    @pytest.mark.parametrize(
        "assertion, result", [(True, {"passed": 1}), (False, {"failed": 1})]
    )
    def test_teardown_error(self, test_file, pytester, assertion, result):
        pytester.makepyfile(test_file(assertion=assertion, teardown="error"))
        page = run(pytester)
        assert_results(page, error=1, **result)

        for test_name in ["test_logging", "test_logging::teardown"]:
            log = get_log(page, test_name)
            for when in ["setup", "test", "teardown"]:
                assert_that(log).matches(self.LOG_LINE_REGEX.format(when))

    def test_no_log(self, test_file, pytester):
        pytester.makepyfile(test_file(assertion=True))
        page = run(pytester)
        assert_results(page, passed=1)

        log = get_log(page, "test_logging")
        assert_that(log).contains("No log output captured.")
        for when in ["setup", "test", "teardown"]:
            assert_that(log).does_not_match(self.LOG_LINE_REGEX.format(when))

    @pytest.mark.usefixtures("log_cli")
    def test_rerun(self, test_file, pytester):
        pytester.makepyfile(
            test_file(assertion=False, flaky="@pytest.mark.flaky(reruns=2)")
        )
        page = run(pytester, query_params={"visible": "failed"})
        assert_results(page, failed=1, rerun=2)

        log = get_log(page)
        assert_that(log.count("Captured log setup")).is_equal_to(3)
        assert_that(log.count("Captured log teardown")).is_equal_to(5)


class TestCollapsedQueryParam:
    @pytest.fixture
    def test_file(self):
        return """
            import pytest
            @pytest.fixture
            def setup():
                error

            def test_error(setup):
                assert True

            def test_pass():
                assert True

            def test_fail():
                assert False
        """

    def test_default(self, pytester, test_file):
        pytester.makepyfile(test_file)
        page = run(pytester)
        assert_results(page, passed=1, failed=1, error=1)

        assert_that(is_collapsed(page, "test_pass")).is_true()
        assert_that(is_collapsed(page, "test_fail")).is_false()
        assert_that(is_collapsed(page, "test_error::setup")).is_false()

    @pytest.mark.parametrize("param", ["failed,error", "FAILED,eRRoR"])
    def test_specified(self, pytester, test_file, param):
        pytester.makepyfile(test_file)
        page = run(pytester, query_params={"collapsed": param})
        assert_results(page, passed=1, failed=1, error=1)

        assert_that(is_collapsed(page, "test_pass")).is_false()
        assert_that(is_collapsed(page, "test_fail")).is_true()
        assert_that(is_collapsed(page, "test_error::setup")).is_true()

    def test_all(self, pytester, test_file):
        pytester.makepyfile(test_file)
        page = run(pytester, query_params={"collapsed": "all"})
        assert_results(page, passed=1, failed=1, error=1)

        for test_name in ["test_pass", "test_fail", "test_error::setup"]:
            assert_that(is_collapsed(page, test_name)).is_true()

    @pytest.mark.parametrize("param", ["", 'collapsed=""', "collapsed=''"])
    def test_falsy(self, pytester, test_file, param):
        pytester.makepyfile(test_file)
        page = run(pytester, query_params={"collapsed": param})
        assert_results(page, passed=1, failed=1, error=1)

        assert_that(is_collapsed(page, "test_pass")).is_false()
        assert_that(is_collapsed(page, "test_fail")).is_false()
        assert_that(is_collapsed(page, "test_error::setup")).is_false()

    @pytest.mark.parametrize("param", ["failed,error", "FAILED,eRRoR"])
    def test_render_collapsed(self, pytester, test_file, param):
        pytester.makeini(
            f"""
            [pytest]
            render_collapsed = {param}
        """
        )
        pytester.makepyfile(test_file)
        page = run(pytester)
        assert_results(page, passed=1, failed=1, error=1)

        assert_that(is_collapsed(page, "test_pass")).is_false()
        assert_that(is_collapsed(page, "test_fail")).is_true()
        assert_that(is_collapsed(page, "test_error::setup")).is_true()

    def test_render_collapsed_precedence(self, pytester, test_file):
        pytester.makeini(
            """
            [pytest]
            render_collapsed = failed,error
        """
        )
        test_file += """
            def test_skip():
                pytest.skip('meh')
        """
        pytester.makepyfile(test_file)
        page = run(pytester, query_params={"collapsed": "skipped"})
        assert_results(page, passed=1, failed=1, error=1, skipped=1)

        assert_that(is_collapsed(page, "test_pass")).is_false()
        assert_that(is_collapsed(page, "test_fail")).is_false()
        assert_that(is_collapsed(page, "test_error::setup")).is_false()
        assert_that(is_collapsed(page, "test_skip")).is_true()
