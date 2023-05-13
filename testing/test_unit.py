import importlib.resources
import os
import sys

import pkg_resources
import pytest
from assertpy import assert_that

pytest_plugins = ("pytester",)


def run(pytester, path="report.html", cmd_flags=None):
    cmd_flags = cmd_flags or []
    path = pytester.path.joinpath(path)
    return pytester.runpytest("--html", path, *cmd_flags)


def file_content():
    try:
        return (
            importlib.resources.files("pytest_html")
            .joinpath("assets", "style.css")
            .read_bytes()
            .decode("utf-8")
            .strip()
        )
    except AttributeError:
        # Needed for python < 3.9
        return pkg_resources.resource_string(
            "pytest_html", os.path.join("assets", "style.css")
        ).decode("utf-8")


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
