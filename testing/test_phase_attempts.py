import base64
import json
from bs4 import BeautifulSoup
import pytest

pytest_plugins = ("pytester",)


@pytest.mark.parametrize("mode", ["assets", "self-contained"])
@pytest.mark.parametrize(
    "case",
    [
        "pass",
        "teardown_error",
        "setup_error",
        "both_errors",
        "setup_skip",
        "call_fail",
        "call_skip",
        "rerun",
    ],
)
def test_phase_extras_public_html(pytester, case, mode):
    pytester.makeconftest(
        """
        import pytest
        from pytest_html import extras

        @pytest.hookimpl(hookwrapper=True)
        def pytest_runtest_makereport(item, call):
            outcome = yield
            report = outcome.get_result()
            attempt = getattr(item, "execution_count", 1)
            report.extras = [extras.html(f'<span>phase-{report.when}-attempt-{attempt}</span>')]
    """
    )
    setup = (
        "raise RuntimeError('setup')"
        if case in ("setup_error", "both_errors")
        else "pytest.skip('setup skip')" if case == "setup_skip" else "pass"
    )
    cleanup = (
        "raise RuntimeError('teardown')"
        if case in ("teardown_error", "both_errors")
        else "pass"
    )
    call = (
        "pytest.skip('call skip')"
        if case == "call_skip"
        else "assert False" if case in ("call_fail", "rerun") else "assert True"
    )
    if case == "rerun":
        code = """
            import pytest
            state = {'n': 0}
            @pytest.mark.flaky(reruns=1)
            def test_case():
                state['n'] += 1
                assert state['n'] == 2
        """
    else:
        code = f"""
            import pytest
            @pytest.fixture
            def thing():
                {setup}
                yield
                {cleanup}

            def test_case(thing):
                {call}
        """
    pytester.makepyfile(code)
    file = pytester.path / "result.html"
    flags = ["--self-contained-html"] if mode == "self-contained" else []
    result = pytester.runpytest("--html", str(file), *flags)
    if case == "pass":
        result.assert_outcomes(passed=1)
    assert file.exists()
    data = json.loads(
        BeautifulSoup(file.read_text(), "html.parser").select_one("#data-container")[
            "data-jsonblob"
        ]
    )
    rows = next(iter(data["tests"].values()))
    got = [[x["content"] for x in row["extras"]] for row in rows]

    def phase(name, attempt=1):
        return f"<span>phase-{name}-attempt-{attempt}</span>"

    expected = {
        "pass": [[phase("setup"), phase("call"), phase("teardown")]],
        "teardown_error": [[phase("setup"), phase("call")], [phase("teardown")]],
        "setup_error": [[phase("setup"), phase("teardown")]],
        # The failing setup prevents executing the fixture's teardown body,
        # although pytest still emits a successful teardown report.
        "both_errors": [[phase("setup"), phase("teardown")]],
        "setup_skip": [[phase("setup"), phase("teardown")]],
        "call_fail": [[phase("setup"), phase("call"), phase("teardown")]],
        "call_skip": [[phase("setup"), phase("call"), phase("teardown")]],
        "rerun": [
            [phase("setup"), phase("call")],
            [phase("setup", 2), phase("call", 2), phase("teardown", 2)],
        ],
    }[case]
    assert got == expected, f"{case} {mode}: expected {expected}, got {got}"


@pytest.mark.parametrize("mode", ["assets", "self-contained"])
def test_no_cross_phase_asset_rows(pytester, mode):
    pytester.makeconftest(
        """
        import pytest
        from pytest_html import extras
        @pytest.hookimpl(hookwrapper=True)
        def pytest_runtest_makereport(item, call):
            result = yield
            report = result.get_result()
            report.extras = [extras.text(f'phase-specific-{report.when}'),
                             extras.json({'phase': report.when})]
    """
    )
    pytester.makepyfile(
        """
        import pytest
        @pytest.fixture
        def broken_teardown():
            yield
            assert False
        def test_ok(broken_teardown):
            pass
    """
    )
    file = pytester.path / "assets-report.html"
    flags = ["--self-contained-html"] if mode == "self-contained" else []
    pytester.runpytest("--html", str(file), *flags)
    data = json.loads(
        BeautifulSoup(file.read_text(), "html.parser").select_one("#data-container")[
            "data-jsonblob"
        ]
    )
    rows = next(iter(data["tests"].values()))
    assert len(rows) == 2
    call, teardown = rows
    assert len(call["extras"]) == 4, f"call extras unexpected: {call['extras']}"
    assert len(teardown["extras"]) == 2
    assert all(
        "teardown" not in extra["content"] for extra in call["extras"]
    ), "extra from visible failed teardown leaked to call"
    assert all(
        "call" not in extra["content"] for extra in teardown["extras"]
    ), "extra from call leaked to teardown"
    if mode == "assets":
        for row in rows:
            for extra in row["extras"]:
                path = pytester.path / extra["content"]
                assert path.exists(), path
                assert path.read_bytes(), path
    else:
        for row in rows:
            for extra in row["extras"]:
                assert extra["content"].startswith("data:"), extra["content"]


@pytest.mark.parametrize("mode", ["assets", "self-contained"])
@pytest.mark.parametrize(
    ("phases", "expected_results", "owned_extras", "expected_logs"),
    [
        (
            [
                ("A", "setup", "passed"),
                ("A", "call", "passed"),
                ("B", "setup", "passed"),
                ("B", "call", "passed"),
                ("B", "teardown", "passed"),
            ],
            ["Passed", "Passed"],
            [["A-setup", "A-call"], ["B-setup", "B-call", "B-teardown"]],
            [[], ["B"]],
        ),
        (
            [
                ("A", "setup", "passed"),
                ("A", "call", "failed"),
                ("B", "setup", "passed"),
                ("B", "call", "passed"),
                ("B", "teardown", "passed"),
            ],
            ["Failed", "Passed"],
            [["A-setup", "A-call"], ["B-setup", "B-call", "B-teardown"]],
            [[], ["B"]],
        ),
        (
            [
                ("A", "setup", "passed"),
                ("A", "call", "passed"),
                ("B", "setup", "passed"),
                ("B", "teardown", "passed"),
            ],
            ["Passed"],
            [["A-setup", "A-call"]],
            [[]],
        ),
        (
            [
                ("A", "setup", "passed"),
                ("A", "call", "passed"),
                ("B", "setup", "failed"),
                ("B", "teardown", "passed"),
            ],
            ["Passed", "Error"],
            [["A-setup", "A-call"], ["B-setup", "B-teardown"]],
            [[], ["B"]],
        ),
        (
            [("A", "setup", "passed")],
            [],
            [],
            [],
        ),
        (
            [("A", "setup", "failed"), ("A", "teardown", "failed")],
            ["Error", "Error"],
            [["A-setup"], ["A-teardown"]],
            [["A"], ["A"]],
        ),
        (
            [("A", "teardown", "failed")],
            ["Error"],
            [["A-teardown"]],
            [["A"]],
        ),
        (
            [
                ("A", "setup", "passed"),
                ("A", "call", "passed"),
                ("A", "teardown", "passed"),
                ("A", "teardown", "passed"),
            ],
            ["Passed"],
            [["A-setup", "A-call", "A-teardown"]],
            [["A"]],
        ),
        (
            [
                ("A", "setup", "passed"),
                ("A", "call", "passed"),
                ("A", "teardown", "passed"),
                ("A", "teardown", "passed"),
                ("B", "setup", "passed"),
                ("B", "call", "passed"),
                ("B", "teardown", "passed"),
            ],
            ["Passed", "Passed"],
            [["A-setup", "A-call", "A-teardown"], ["B-setup", "B-call", "B-teardown"]],
            [["A"], ["B"]],
        ),
        (
            [
                ("A", "setup", "passed"),
                ("A", "call", "passed"),
                ("A", "teardown", "passed"),
                ("B", "setup", "passed"),
                ("B", "call", "passed"),
                ("B", "teardown", "passed"),
            ],
            ["Passed", "Passed"],
            [["A-setup", "A-call", "A-teardown"], ["B-setup", "B-call", "B-teardown"]],
            [["A"], ["B"]],
        ),
    ],
)
def test_synthetic_phase_stream(
    pytester, mode, phases, expected_results, owned_extras, expected_logs
):
    pytester.makeconftest(
        f"""
        import base64
        import pytest
        from pytest_html import extras

        PHASES = {phases!r}

        @pytest.hookimpl(tryfirst=True)
        def pytest_runtest_protocol(item, nextitem):
            for attempt, phase, outcome in PHASES:
                report = pytest.TestReport(
                    nodeid=item.nodeid, location=item.location, keywords={{}},
                    outcome=outcome, longrepr=None, when=phase,
                    duration=0.01,
                    sections=[('Captured stdout teardown', f'capture-{{attempt}}')]
                    if phase == 'teardown' else [],
                )
                marker = f'{{attempt}}-{{phase}}'
                report.extras = [
                    extras.html(f'<b>{{marker}}</b>'),
                    extras.text(marker),
                    extras.json({{'marker': marker}}),
                    extras.image(base64.b64encode(marker.encode()).decode(), mime_type='image/png'),
                ]
                item.ihook.pytest_runtest_logreport(report=report)
            return True
        """
    )
    pytester.makepyfile("def test_case(): pass")
    pytester.makeini("[pytest]\ngenerate_report_on_test = true")
    report = pytester.path / "report.html"
    flags = ["--self-contained-html"] if mode == "self-contained" else []
    pytester.runpytest("--html", str(report), *flags)
    document = BeautifulSoup(report.read_text(encoding="utf-8"), "html.parser")
    blob = json.loads(document.select_one("#data-container")["data-jsonblob"])
    rows = [row for node_rows in blob["tests"].values() for row in node_rows]
    assert [row["result"] for row in rows] == expected_results
    assert [
        [extra["content"] for extra in row["extras"] if extra["format_type"] == "html"]
        for row in rows
    ] == [[f"<b>{marker}</b>" for marker in markers] for markers in owned_extras]

    if not expected_results:
        assert not list((pytester.path / "assets").glob("*__setup_*.txt"))

    for row, expected_markers, log_owners in zip(rows, owned_extras, expected_logs):
        for attempt in "AB":
            assert (f"capture-{attempt}" in row["log"]) == (attempt in log_owners)
        assert len(row["extras"]) == 4 * len(expected_markers)
        for marker_index, marker in enumerate(expected_markers):
            phase = marker.split("-", 1)[1]
            suffix = "0" if marker.startswith("A-") else "-1"
            basename = "test_synthetic_phase_stream.py__test_case"
            if phase != "call":
                basename += f"__{phase}"
            group = row["extras"][marker_index * 4 : (marker_index + 1) * 4]
            assert [entry["format_type"] for entry in group] == [
                "html",
                "text",
                "json",
                "image",
            ]
            assert group[0]["content"] == f"<b>{marker}</b>"
            files = [
                ("txt", "text/plain", marker.encode()),
                ("json", "application/json", json.dumps({"marker": marker}).encode()),
                ("png", "image/png", marker.encode()),
            ]
            for extra_index, (
                entry,
                (extension, mime_type, expected_bytes),
            ) in enumerate(zip(group[1:], files), start=1):
                assert entry["mime_type"] == mime_type
                expected_name = f"{basename}_{extra_index}_{suffix}.{extension}"
                if mode == "assets":
                    assert entry["content"] == f"assets/{expected_name}"
                    assert (
                        pytester.path / entry["content"]
                    ).read_bytes() == expected_bytes
                else:
                    prefix = f"data:{mime_type}"
                    if entry["format_type"] != "image":
                        prefix += ";charset=utf-8"
                    assert entry["content"].startswith(prefix + ";base64,")
                    assert (
                        base64.b64decode(entry["content"].partition(",")[2])
                        == expected_bytes
                    )


@pytest.mark.parametrize("mode", ["assets", "self-contained"])
def test_removed_attempt_row_cannot_receive_teardown_log(pytester, mode):
    pytester.makeconftest(
        """
        import pytest

        @pytest.hookimpl(tryfirst=True)
        def pytest_runtest_protocol(item, nextitem):
            for attempt in ('A', 'B'):
                for phase in ('setup', 'call', 'teardown'):
                    report = pytest.TestReport(
                        nodeid=item.nodeid, location=item.location,
                        keywords={}, outcome='passed', longrepr=None,
                        when=phase, duration=0.01,
                        sections=[('Captured stdout teardown', f'capture-{attempt}')]
                        if phase == 'teardown' else [],
                    )
                    report.attempt_marker = attempt
                    item.ihook.pytest_runtest_logreport(report=report)
            return True

        def pytest_html_results_table_row(report, cells):
            if report.when == 'call' and getattr(report, 'attempt_marker', '') == 'B':
                cells.clear()
        """
    )
    pytester.makepyfile("def test_case(): pass")
    report = pytester.path / "report.html"
    flags = ["--self-contained-html"] if mode == "self-contained" else []
    pytester.runpytest("--html", str(report), *flags)
    document = BeautifulSoup(report.read_text(encoding="utf-8"), "html.parser")
    data = json.loads(document.select_one("#data-container")["data-jsonblob"])
    rows = next(iter(data["tests"].values()))
    assert len(rows) == 1
    assert rows[0]["result"] == "Passed"
    assert "capture-A" in rows[0]["log"]
    assert "capture-B" not in rows[0]["log"]


@pytest.mark.parametrize("mode", ["assets", "self-contained"])
def test_explicit_retry_does_not_consume_implicit_asset_suffix(pytester, mode):
    pytester.makeconftest(
        """
        import pytest
        from pytest_html import extras

        @pytest.hookimpl(tryfirst=True)
        def pytest_runtest_protocol(item, nextitem):
            for attempt, rerun in enumerate((0, None, None)):
                for phase in ('setup', 'call', 'teardown'):
                    report = pytest.TestReport(
                        nodeid=item.nodeid, location=item.location,
                        keywords={}, outcome='passed', longrepr=None,
                        when=phase, duration=0.01, sections=[],
                    )
                    # An unmarked setup can precede a plugin-marked call.
                    if rerun is not None and phase != 'setup':
                        report.rerun = rerun
                    report.extras = [extras.text(f'attempt-{attempt}-{phase}')]
                    item.ihook.pytest_runtest_logreport(report=report)
            return True
        """
    )
    pytester.makepyfile("def test_case(): pass")
    path = pytester.path / "report.html"
    flags = ["--self-contained-html"] if mode == "self-contained" else []
    pytester.runpytest("--html", str(path), *flags)
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    rows = next(
        iter(
            json.loads(soup.select_one("#data-container")["data-jsonblob"])[
                "tests"
            ].values()
        )
    )
    assert [row["result"] for row in rows] == ["Passed"] * 3
    for attempt, (row, suffix) in enumerate(zip(rows, ("1", "0", "-1"))):
        assert len(row["extras"]) == 3
        for phase, extra in zip(("setup", "call", "teardown"), row["extras"]):
            payload = f"attempt-{attempt}-{phase}".encode()
            if mode == "assets":
                assert extra["content"].endswith(f"_0_{suffix}.txt")
                assert (pytester.path / extra["content"]).read_bytes() == payload
            else:
                assert extra["content"].startswith(
                    "data:text/plain;charset=utf-8;base64,"
                )
                assert base64.b64decode(extra["content"].partition(",")[2]) == payload


@pytest.mark.parametrize("mode", ["assets", "self-contained"])
def test_distinct_failed_teardown_after_completed_attempt_is_visible(pytester, mode):
    pytester.makeconftest(
        """
        import pytest
        from pytest_html import extras

        @pytest.hookimpl(tryfirst=True)
        def pytest_runtest_protocol(item, nextitem):
            for when, outcome, label in (
                ('setup', 'passed', 'first-setup'),
                ('call', 'passed', 'first-call'),
                ('teardown', 'passed', 'first-teardown'),
                ('teardown', 'failed', 'second-teardown'),
            ):
                report = pytest.TestReport(
                    nodeid=item.nodeid, location=item.location, keywords={},
                    outcome=outcome, longrepr='distinct teardown failed'
                    if outcome == 'failed' else None,
                    when=when, duration=0.01,
                    sections=[('Captured stdout teardown', label)]
                    if when == 'teardown' else [],
                )
                report.extras = [extras.text(label)]
                item.ihook.pytest_runtest_logreport(report=report)
            return True
        """
    )
    pytester.makepyfile("def test_case(): pass")
    pytester.makeini("[pytest]\ngenerate_report_on_test = true")
    path = pytester.path / "report.html"
    flags = ["--self-contained-html"] if mode == "self-contained" else []
    pytester.runpytest("--html", str(path), *flags)
    document = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    data = json.loads(document.select_one("#data-container")["data-jsonblob"])
    rows = next(iter(data["tests"].values()))
    assert [row["result"] for row in rows] == ["Passed", "Error"]
    assert [len(row["extras"]) for row in rows] == [3, 1]
    assert "first-teardown" in rows[0]["log"]
    assert "second-teardown" not in rows[0]["log"]
    assert "second-teardown" in rows[1]["log"]
    for row, payloads in zip(
        rows, (("first-setup", "first-call", "first-teardown"), ("second-teardown",))
    ):
        for extra, payload in zip(row["extras"], payloads):
            assert extra["format_type"] == "text"
            if mode == "assets":
                assert (
                    pytester.path / extra["content"]
                ).read_bytes() == payload.encode()
            else:
                assert (
                    base64.b64decode(extra["content"].partition(",")[2])
                    == payload.encode()
                )


@pytest.mark.parametrize("mode", ["assets", "self-contained"])
def test_replaying_same_call_report_object_is_exactly_once(pytester, mode):
    pytester.makeconftest(
        """
        import pytest
        from pytest_html import extras

        @pytest.hookimpl(tryfirst=True)
        def pytest_runtest_protocol(item, nextitem):
            for when in ('setup', 'call', 'teardown'):
                report = pytest.TestReport(
                    nodeid=item.nodeid, location=item.location, keywords={},
                    outcome='passed', longrepr=None, when=when, duration=0.01,
                    sections=[],
                )
                report.extras = [extras.text(f'once-{when}')]
                item.ihook.pytest_runtest_logreport(report=report)
                if when == 'call':
                    # A hook redelivers the identical report object before teardown.
                    item.ihook.pytest_runtest_logreport(report=report)
            return True
        """
    )
    pytester.makepyfile("def test_case(): pass")
    pytester.makeini("[pytest]\ngenerate_report_on_test = true")
    path = pytester.path / "report.html"
    flags = ["--self-contained-html"] if mode == "self-contained" else []
    pytester.runpytest("--html", str(path), *flags)
    document = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    data = json.loads(document.select_one("#data-container")["data-jsonblob"])
    rows = next(iter(data["tests"].values()))
    assert [row["result"] for row in rows] == ["Passed"]
    assert len(rows[0]["extras"]) == 3
    for extra, payload in zip(
        rows[0]["extras"], ("once-setup", "once-call", "once-teardown")
    ):
        assert extra["format_type"] == "text"
        if mode == "assets":
            assert (pytester.path / extra["content"]).read_bytes() == payload.encode()
        else:
            assert (
                base64.b64decode(extra["content"].partition(",")[2]) == payload.encode()
            )
