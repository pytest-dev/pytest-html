from __future__ import annotations

from pathlib import Path

import pytest

pytest_plugins = ("pytester",)


def run(pytester, path="report.html", cmd_flags=None):
    cmd_flags = cmd_flags or []
    path = pytester.path.joinpath(path)
    return pytester.runpytest("--html", path, *cmd_flags)


class TestBuiltinClassicTheme:
    def test_default_theme_generates_report(self, pytester):
        pytester.makepyfile("def test_pass(): pass")
        result = run(pytester)
        result.assert_outcomes(passed=1)
        assert (pytester.path / "report.html").exists()

    def test_explicit_classic_theme(self, pytester):
        pytester.makeini("[pytest]\nhtml_theme = classic")
        pytester.makepyfile("def test_pass(): pass")
        result = run(pytester)
        result.assert_outcomes(passed=1)
        report = (pytester.path / "report.html").read_text()
        assert "pytest-html" in report


class TestBuiltinModernTheme:
    def test_modern_theme_generates_report(self, pytester):
        pytester.makeini("[pytest]\nhtml_theme = modern")
        pytester.makepyfile("def test_pass(): pass")
        result = run(pytester)
        result.assert_outcomes(passed=1)
        report = (pytester.path / "report.html").read_text()
        assert "modern-header" in report
        assert "stat-card" in report

    def test_modern_theme_uses_modern_css(self, pytester):
        pytester.makeini("[pytest]\nhtml_theme = modern")
        pytester.makepyfile("def test_pass(): pass")
        result = run(pytester)
        result.assert_outcomes(passed=1)
        css_path = pytester.path / "assets" / "style.css"
        css = css_path.read_text()
        assert ".dashboard" in css
        assert ".stat-card" in css


class TestThemePath:
    def test_ini_theme_path_overrides_entry_points(self, pytester):
        theme_dir = pytester.path / "my_theme"
        theme_dir.mkdir()
        (theme_dir / "layout.jinja2").write_text(
            '{% extends "base.jinja2" %}\n'
            "{% block header %}\n"
            '<h1 id="title">CUSTOM THEME: {{ title }}</h1>\n'
            "{% endblock header %}\n"
        )
        pytester.makeini(
            f"[pytest]\nhtml_theme_path = {theme_dir}\n"
        )
        pytester.makepyfile("def test_pass(): pass")
        result = run(pytester)
        result.assert_outcomes(passed=1)
        report = (pytester.path / "report.html").read_text()
        assert "CUSTOM THEME:" in report

    def test_theme_path_with_custom_css(self, pytester):
        theme_dir = pytester.path / "my_theme"
        theme_dir.mkdir()
        (theme_dir / "layout.jinja2").write_text('{% extends "base.jinja2" %}\n')
        (theme_dir / "style.css").write_text("body { background: pink; }\n")
        pytester.makeini(
            f"[pytest]\nhtml_theme_path = {theme_dir}\n"
        )
        pytester.makepyfile("def test_pass(): pass")
        result = run(pytester)
        result.assert_outcomes(passed=1)
        css_path = pytester.path / "assets" / "style.css"
        css = css_path.read_text()
        assert "background: pink" in css

    def test_theme_path_without_layout_raises_error(self, pytester):
        theme_dir = pytester.path / "bad_theme"
        theme_dir.mkdir()
        pytester.makeini(
            f"[pytest]\nhtml_theme_path = {theme_dir}\n"
        )
        pytester.makepyfile("def test_pass(): pass")
        result = run(pytester)
        result.stderr.fnmatch_lines(["*does not contain layout.jinja2*"])

    def test_theme_path_falls_back_to_classic_css(self, pytester):
        theme_dir = pytester.path / "minimal_theme"
        theme_dir.mkdir()
        (theme_dir / "layout.jinja2").write_text('{% extends "base.jinja2" %}\n')
        pytester.makeini(
            f"[pytest]\nhtml_theme_path = {theme_dir}\n"
        )
        pytester.makepyfile("def test_pass(): pass")
        result = run(pytester)
        result.assert_outcomes(passed=1)
        css_path = pytester.path / "assets" / "style.css"
        css = css_path.read_text()
        assert "font-family: Helvetica" in css


class TestThemeNotFound:
    def test_unknown_theme_raises_error(self, pytester):
        pytester.makeini("[pytest]\nhtml_theme = nonexistent")
        pytester.makepyfile("def test_pass(): pass")
        result = run(pytester)
        result.stderr.fnmatch_lines(["*Unknown html_theme 'nonexistent'*"])


class TestThemeWithExtraCss:
    def test_extra_css_appended_to_theme_css(self, pytester):
        pytester.makeini("[pytest]\nhtml_theme = modern")
        extra_css = pytester.path / "extra.css"
        extra_css.write_text("body { margin: 99px; }\n")
        pytester.makepyfile("def test_pass(): pass")
        result = run(pytester, cmd_flags=["--css", str(extra_css)])
        result.assert_outcomes(passed=1)
        css_path = pytester.path / "assets" / "style.css"
        css = css_path.read_text()
        assert ".dashboard" in css
        assert "margin: 99px" in css
