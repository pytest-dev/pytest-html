import importlib.resources
import sys
from pathlib import Path

import pytest
from assertpy import assert_that

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


@pytest.fixture
def text_extra(pytester):
    pytester.makeconftest(
        """
        import pytest

        @pytest.hookimpl(hookwrapper=True)
        def pytest_runtest_makereport(item, call):
            outcome = yield
            report = outcome.get_result()
            if report.when == "call":
                from pytest_html import extras
                report.extras = [extras.text("content")]
    """
    )


@pytest.mark.parametrize(
    "test_file, asset_name",
    [
        ("def test_pass(): pass", "test_pass_0_0.txt"),
        ("def test_pässed(): pass", "test_pässed_0_0.txt"),
        (
            """
            import pytest
            @pytest.mark.parametrize("value", ["ä"])
            def test_pass(value): pass
            """,
            "test_pass_ä__0_0.txt",
        ),
    ],
    ids=["ascii", "non-ascii-name", "non-ascii-param"],
)
def test_extra_asset_name(pytester, text_extra, test_file, asset_name):
    pytester.makepyfile(test_extra_asset_name=test_file)
    result = run(pytester)
    result.assert_outcomes(passed=1)

    path = pytester.path.joinpath("assets", f"test_extra_asset_name.py__{asset_name}")
    assert_that(str(path)).exists()


def test_extra_asset_name_invalid_escape_sequence(pytester, text_extra):
    pytester.makeini(
        """
        [pytest]
        disable_test_id_escaping_and_forfeit_all_rights_to_community_support = true
    """
    )
    pytester.makepyfile(
        test_extra_asset_name=r"""
        import pytest
        @pytest.mark.parametrize("path", ["C:\\New Folder"])
        def test_pass(path): pass
        """
    )
    result = run(pytester)
    result.assert_outcomes(passed=1)

    path = pytester.path.joinpath(
        "assets", "test_extra_asset_name.py__test_pass_C__New_Folder__0_0.txt"
    )
    assert_that(str(path)).exists()
