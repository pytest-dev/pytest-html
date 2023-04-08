pytest_plugins = ("pytester",)


def run(pytester, path="report.html", *args):
    path = pytester.path.joinpath(path)
    return pytester.runpytest("--html", path, *args)


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
    result.stdout.fnmatch_lines(
        [
            "*DeprecationWarning: 'duration_formatter'*",
        ],
    )
