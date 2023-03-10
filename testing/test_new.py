import base64
import importlib.resources
import json
import os
import random
import re
from base64 import b64encode
from pathlib import Path

import pkg_resources
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


def run(pytester, path="report.html", *args):
    path = pytester.path.joinpath(path)
    pytester.runpytest("-s", "--html", path, *args)

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920x1080")
    # chrome_options.add_argument("--allow-file-access-from-files")
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

        driver.get(f"file:///reports{path}")
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
            assert_that(result).is_equal_to(f"{number} {OUTCOMES[outcome]}")

    # if total_tests is not None:
    #     number_of_tests = total_tests
    # total = get_text(page, "p[class='run-count']")
    # expr = r"%d %s ran in \d+.\d+ seconds."
    # % (number_of_tests, "tests" if number_of_tests > 1 else "test")
    # assert_that(total).matches(expr)


def get_element(page, selector):
    return page.select_one(selector)


def get_text(page, selector):
    return get_element(page, selector).string


def get_log(page):
    # TODO(jim) move to get_text (use .contents)
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
        if pause < 1:
            assert_that(int(duration.replace("ms", ""))).is_between(
                expectation, expectation * 2
            )
        else:
            assert_that(duration).matches(expectation)

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
                pytest.skip('{reason}')
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

    def test_xfail(self, pytester):
        reason = str(random.random())
        pytester.makepyfile(
            f"""
            import pytest
            def test_xfail():
                pytest.xfail('{reason}')
        """
        )
        page = run(pytester)
        assert_results(page, xfailed=1)
        assert_that(get_log(page)).contains(reason)

    def test_xpass(self, pytester):
        pytester.makepyfile(
            """
            import pytest
            @pytest.mark.xfail()
            def test_xpass():
                pass
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
        page = run(pytester, "report.html", "--self-contained-html")

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
        page = run(pytester, "report.html", "--self-contained-html")

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
        page = run(pytester, "report.html", "--self-contained-html")

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
        page = run(pytester, "report.html", "--self-contained-html")

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
        page = run(pytester, "report.html", "--self-contained-html")

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
        page = run(pytester, "report.html", "-n1")
        assert_results(page, passed=1)
