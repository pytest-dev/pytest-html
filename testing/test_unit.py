pytest_plugins = ("pytester",)


def run(pytester, path="report.html", cmd_flags=None):
    cmd_flags = cmd_flags or []
    path = pytester.path.joinpath(path)
    return pytester.runpytest("--html", path, *cmd_flags)


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
