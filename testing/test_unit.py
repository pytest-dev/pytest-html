import importlib.resources
import json
import sys
from pathlib import Path

import pytest
from assertpy import assert_that
from bs4 import BeautifulSoup

pytest_plugins = ("pytester",)


def run(pytester, path="report.html", cmd_flags=None):
    cmd_flags = cmd_flags or []
    path = pytester.path.joinpath(path)
    return pytester.runpytest("--html", path, *cmd_flags)


def file_content():
    return (
        importlib.resources.files("pytest_html")
        .joinpath("assets", "style.css")
        .read_bytes()
        .decode("utf-8")
        .strip()
    )


def test_duration_format_deprecation_warning(pytester):
    pytester.makeconftest(
        """
        import pytest
        @pytest.hookimpl(hookwrapper=True)
        def pytest_runtest_makereport(item, call):
            outcome = yield
            report = outcome.get_result()
            setattr(report, "duration_formatter", "%H:%M:%S.%f")
    """
    )
    pytester.makepyfile("def test_pass(): pass")
    result = run(pytester)
    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(
        [
            "*DeprecationWarning: 'duration_formatter'*",
        ],
    )


def test_html_results_summary_hook(pytester):
    pytester.makeconftest(
        """
        import pytest

        def pytest_html_results_summary(prefix, summary, postfix, session):
            print(prefix)
            print(summary)
            print(postfix)
            print(session)
    """
    )

    pytester.makepyfile("def test_pass(): pass")
    result = run(pytester)
    result.assert_outcomes(passed=1)


def test_chdir(pytester):
    pytester.makepyfile(
        """
        import pytest

        @pytest.fixture
        def changing_dir(tmp_path, monkeypatch):
            monkeypatch.chdir(tmp_path)

        def test_function(changing_dir):
            pass
    """
    )
    report_path = Path("reports") / "report.html"
    page = pytester.runpytest("--html", str(report_path))
    assert page.ret == 0
    assert (
        f"Generated html report: {(pytester.path / report_path).as_uri()}"
    ) in page.outlines[-2]


@pytest.fixture
def css_file_path(pytester):
    css_one = """
        h1 {
          color: red;
        }
    """
    css_two = """
        h2 {
          color: blue;
        }
    """
    css_dir = pytester.path / "extra_css"
    css_dir.mkdir()
    file_path = css_dir / "one.css"
    with open(file_path, "w") as f:
        f.write(css_one)

    pytester.makefile(".css", two=css_two)
    pytester.makepyfile("def test_pass(): pass")

    return file_path


@pytest.fixture(params=[True, False])
def expandvar(request, css_file_path, monkeypatch):
    if request.param:
        monkeypatch.setenv("EXTRA_CSS", str(css_file_path))
        return "%EXTRA_CSS%" if sys.platform == "win32" else "${EXTRA_CSS}"
    return css_file_path


def test_custom_css(pytester, css_file_path, expandvar):
    result = run(
        pytester, "report.html", cmd_flags=["--css", expandvar, "--css", "two.css"]
    )
    result.assert_outcomes(passed=1)

    path = pytester.path.joinpath("assets", "style.css")

    with open(str(path)) as f:
        css = f.read()
        assert_that(css).contains("* " + str(css_file_path)).contains("* two.css")


def test_custom_css_selfcontained(pytester, css_file_path, expandvar):
    result = run(
        pytester,
        "report.html",
        cmd_flags=[
            "--css",
            expandvar,
            "--css",
            "two.css",
            "--self-contained-html",
        ],
    )
    result.assert_outcomes(passed=1)

    with open(pytester.path / "report.html") as f:
        html = f.read()
        assert_that(html).contains("* " + str(css_file_path)).contains("* two.css")


def test_html_in_test_id_is_escaped(pytester):
    pytester.makepyfile(
        """
        import pytest


        @pytest.mark.parametrize("value", ["<b>pwned</b>"])
        def test_id_escaping(value):
            pass
    """
    )
    result = run(pytester)
    result.assert_outcomes(passed=1)

    html = (pytester.path / "report.html").read_text(encoding="utf-8")
    blob = BeautifulSoup(html, "html.parser").find(id="data-container")["data-jsonblob"]
    tests = json.loads(blob)["tests"]
    nodeid = next(key for key in tests if "test_id_escaping" in key)
    row = tests[nodeid][0]["resultsTableRow"]
    test_id_cell = next(cell for cell in row if "col-testId" in cell)

    assert_that(test_id_cell).does_not_contain("<b>pwned</b>").contains(
        "&lt;b&gt;pwned&lt;/b&gt;"
    )
