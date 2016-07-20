# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

from base64 import b64encode
import datetime
import json
import os
import pkg_resources
import platform
import sys
import time
import bisect
import hashlib

import pytest
from py.xml import html, raw

from . import extras

PY3 = sys.version_info[0] == 3

# Python 2.X and 3.X compatibility
if PY3:
    from html import escape
else:
    from codecs import open
    from cgi import escape


@pytest.fixture(scope='session', autouse=True)
def environment(request):
    """Provide environment details for HTML report"""
    request.config._environment.extend([
        ('Python', platform.python_version()),
        ('Platform', platform.platform())])


def pytest_addoption(parser):
    group = parser.getgroup('terminal reporting')
    group.addoption('--html', action='store', dest='htmlpath',
                    metavar='path', default=None,
                    help='create html report file at given path.')
    group.addoption('--self-contained-html', action='store_true',
                    help='create a self-contained html file containing all '
                    'necessary styles, scripts, and images - this means '
                    'that the report may not render or function where CSP '
                    'restrictions are in place (see '
                    'https://developer.mozilla.org/docs/Web/Security/CSP)')


def pytest_configure(config):
    config._environment = []
    htmlpath = config.option.htmlpath
    # prevent opening htmlpath on slave nodes (xdist)
    if htmlpath and not hasattr(config, 'slaveinput'):
        contained_html = config.getoption('self_contained_html')
        config._html = HTMLReport(htmlpath, contained_html=contained_html)
        config.pluginmanager.register(config._html)
    if hasattr(config, 'slaveoutput'):
        config.slaveoutput['environment'] = config._environment


@pytest.mark.optionalhook
def pytest_testnodedown(node):
    # note that any environments from remote slaves will be replaced with the
    # environment from the final slave to quit
    if hasattr(node, 'slaveoutput'):
        node.config._environment = node.slaveoutput['environment']


def pytest_unconfigure(config):
    html = getattr(config, '_html', None)
    if html:
        del config._html
        config.pluginmanager.unregister(html)


def data_uri(content, mime_type='text/plain', charset='utf-8'):
    if PY3:
        data = b64encode(content.encode(charset)).decode('ascii')
    else:
        data = b64encode(content)
    return 'data:{0};charset={1};base64,{2}'.format(mime_type, charset, data)


class HTMLReport(object):

    def __init__(self, logfile, **kwargs):
        logfile = os.path.expanduser(os.path.expandvars(logfile))
        self.logfile = os.path.abspath(logfile)
        self.test_logs = []
        self.results = []
        self.errors = self.failed = 0
        self.passed = self.skipped = 0
        self.xfailed = self.xpassed = 0
        self.rerun = 0
        self.contained_html = kwargs['contained_html']

    class TestResult:

        def __init__(self, outcome, report, contained_html, logfile):
            self.test_id = report.nodeid
            if report.when != 'call':
                self.test_id = '::'.join([report.nodeid, report.when])
            self.time = getattr(report, 'duration', 0.0)
            self.outcome = outcome
            self.additional_html = []
            self.links_html = []
            self.contained_html = contained_html
            self.logfile = logfile

            for extra in getattr(report, 'extra', []):
                self.append_extra_html(extra)

            self.append_log_html(report, self.additional_html)

            self.row_table = html.tr([
                html.td(self.outcome, class_='col-result'),
                html.td(self.test_id, class_='col-name'),
                html.td('{0:.2f}'.format(self.time), class_='col-duration'),
                html.td(self.links_html, class_='col-links')])

            self.row_extra = html.tr(html.td(self.additional_html,
                                     class_='extra', colspan='5'))

        def __lt__(self, other):
            order = ('Error', 'Failed', 'Rerun', 'XFailed',
                     'XPassed', 'Skipped', 'Passed')
            return order.index(self.outcome) < order.index(other.outcome)

        def append_extra_html(self, extra):
            href = None
            if extra.get('format') == extras.FORMAT_IMAGE:
                image_src = None
                if self.contained_html:
                    image_src = 'data:image/png;base64,{0}'.format(
                            extra.get('content'))
                    href = '#'
                else:
                    hash_key = self.test_id + self.outcome
                    hash_generator = hashlib.md5()
                    hash_generator.update(hash_key)
                    image_file_name = '{0}.jpg'.format(hash_generator.digest)

                    super_dir_name = os.path.dirname(self.logfile)
                    dir_name = os.path.join(super_dir_name, 'assets')
                    image_path = os.path.join(dir_name, image_file_name)
                    href = os.path.join('assets', image_file_name)
                    image_src = href

                    with open(image_path, 'w') as fh:
                        fh.write(extra.get('content').decode('base64'))

                self.additional_html.append(html.div(
                    html.a(html.img(src=image_src), href=href),
                    class_='image'))

            elif extra.get('format') == extras.FORMAT_HTML:
                self.additional_html.append(html.div(
                                            raw(extra.get('content'))))

            elif extra.get('format') == extras.FORMAT_JSON:
                href = data_uri(json.dumps(extra.get('content')),
                                mime_type='application/json')

            elif extra.get('format') == extras.FORMAT_TEXT:
                href = data_uri(extra.get('content'))

            elif extra.get('format') == extras.FORMAT_URL:
                href = extra.get('content')

            if href is not None:
                self.links_html.append(html.a(
                    extra.get('name'),
                    class_=extra.get('format'),
                    href=href,
                    target='_blank'))
                self.links_html.append(' ')

        def append_log_html(self, report, additional_html):
            log = html.div(class_='log')
            if report.longrepr:
                for line in str(report.longrepr).splitlines():
                    if not PY3:
                        line = line.decode('utf-8')
                    separator = line.startswith('_ ' * 10)
                    if separator:
                        log.append(line[:80])
                    else:
                        exception = line.startswith("E   ")
                        if exception:
                            log.append(html.span(raw(escape(line)),
                                                 class_='error'))
                        else:
                            log.append(raw(escape(line)))
                    log.append(html.br())

            for header, content in report.sections:
                log.append(' {0} '.format(header).center(80, '-'))
                log.append(html.br())
                log.append(content)

            if len(log) == 0:
                log = html.div(class_='empty log')
                log.append('No log output captured.')
            additional_html.append(log)

    def _appendrow(self, outcome, report):
        result = self.TestResult(outcome, report, self.contained_html,
                                 self.logfile)
        index = bisect.bisect_right(self.results, result)
        self.results.insert(index, result)
        self.test_logs.insert(index, html.tbody(result.row_table,
                              result.row_extra, class_=result.outcome.lower() +
                              ' results-table-row'))

    def append_passed(self, report):
        if report.when == 'call':
            self.passed += 1
            self._appendrow('Passed', report)

    def append_failed(self, report):
        if report.when == "call":
            if hasattr(report, "wasxfail"):
                self.xpassed += 1
                self._appendrow('XPassed', report)
            else:
                self.failed += 1
                self._appendrow('Failed', report)
        else:
            self.errors += 1
            self._appendrow('Error', report)

    def append_skipped(self, report):
        if hasattr(report, "wasxfail"):
            self.xfailed += 1
            self._appendrow('XFailed', report)
        else:
            self.skipped += 1
            self._appendrow('Skipped', report)

    def append_other(self, report):
        # For now, the only "other" the plugin give support is rerun
        self.rerun += 1
        self._appendrow('Rerun', report)

    def _generate_report(self, session):
        suite_stop_time = time.time()
        suite_time_delta = suite_stop_time - self.suite_start_time
        numtests = self.passed + self.failed + self.xpassed + self.xfailed
        generated = datetime.datetime.now()

        self.style_css = pkg_resources.resource_string(
            __name__, os.path.join('resources', 'style.css'))
        if PY3:
            self.style_css = self.style_css.decode('utf-8')

        css_href = os.path.join('assets', 'style.css')
        html_css = html.link(href=css_href, rel='stylesheet',
                             type='text/css')
        if session.config.getoption('self_contained_html'):
            html_css = html.style(raw(self.style_css))

        head = html.head(
            html.meta(charset='utf-8'),
            html.title('Test Report'),
            html_css)

        class Outcome:

            def __init__(self, outcome, total=0, label=None,
                         test_result=None, class_html=None):
                self.outcome = outcome
                self.label = label or outcome
                self.class_html = class_html or outcome
                self.total = total
                self.test_result = test_result or outcome

                self.generate_checkbox()
                self.generate_summary_item()

            def generate_checkbox(self):
                checkbox_kwargs = {'data-test-result':
                                   self.test_result.lower()}
                if self.total == 0:
                    checkbox_kwargs['disabled'] = 'true'

                self.checkbox = html.input(type='checkbox',
                                           checked='true',
                                           onChange='filter_table(this)',
                                           name='filter_checkbox',
                                           **checkbox_kwargs)

            def generate_summary_item(self):
                self.summary_item = html.span('{0} {1}'.
                                              format(self.total, self.label),
                                              class_=self.class_html)

        outcomes = [Outcome('passed', self.passed),
                    Outcome('skipped', self.skipped),
                    Outcome('failed', self.failed),
                    Outcome('error', self.errors, label='errors'),
                    Outcome('xfailed', self.xfailed,
                            label='expected failures'),
                    Outcome('xpassed', self.xpassed,
                            label='unexpected passes'),
                    Outcome('rerun', self.rerun)]

        summary = [html.h2('Summary'), html.p(
            '{0} tests ran in {1:.2f} seconds. '.format(
                numtests, suite_time_delta)),
            html.p('(Un)check the boxes to filter the results.')]

        for outcome in outcomes:
            summary.append(outcome.checkbox)
            summary.append(outcome.summary_item)
            summary.append(' ')

        results = [html.h2('Results'), html.table([html.thead(
            html.tr([
                html.th('Result',
                        class_='sortable result initial-sort',
                        col='result'),
                html.th('Test', class_='sortable', col='name'),
                html.th('Duration',
                        class_='sortable numeric',
                        col='duration'),
                html.th('Links')]),
            html.tr([
                html.th('No results found. Try to check the filters',
                    colspan='5')],
                    id='not-found-message', hidden='true'),
            id='results-table-head'),
                self.test_logs],  id='results-table')]

        main_js = pkg_resources.resource_string(
            __name__, os.path.join('resources', 'main.js'))
        if PY3:
            main_js = main_js.decode('utf-8')

        body = html.body(
            html.script(raw(main_js)),
            html.p('Report generated on {0} at {1}'.format(
                generated.strftime('%d-%b-%Y'),
                generated.strftime('%H:%M:%S'))))

        if session.config._environment:
            environment = set(session.config._environment)
            body.append(html.h2('Environment'))
            body.append(html.table(
                [html.tr(html.td(e[0]), html.td(e[1])) for e in sorted(
                    environment, key=lambda e: e[0]) if e[1]],
                id='environment'))

        body.extend(summary)
        body.extend(results)

        doc = html.html(head, body)

        unicode_doc = u'<!DOCTYPE html>\n{0}'.format(doc.unicode(indent=2))
        if PY3:
            # Fix encoding issues, e.g. with surrogates
            unicode_doc = unicode_doc.encode('utf-8',
                                             errors='xmlcharrefreplace')
            unicode_doc = unicode_doc.decode('utf-8')
        return unicode_doc

    def _save_report(self, report_content, self_contained_html):
        dir_name = os.path.dirname(self.logfile)
        assets_dir = os.path.join(dir_name, 'assets')
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        if not os.path.exists(assets_dir):
            os.makedirs(assets_dir)
        with open(self.logfile, 'w', encoding='utf-8') as f:
            f.write(report_content)
        if not self_contained_html:
            style_path = os.path.join(assets_dir, 'style.css')
            with open(style_path, 'w', encoding='utf-8') as f:
                f.write(self.style_css)

    def pytest_runtest_logreport(self, report):
        if report.passed:
            self.append_passed(report)
        elif report.failed:
            self.append_failed(report)
        elif report.skipped:
            self.append_skipped(report)
        else:
            self.append_other(report)

    def pytest_sessionstart(self, session):
        self.suite_start_time = time.time()

    def pytest_sessionfinish(self, session):
        report_content = self._generate_report(session)
        self_contained_html = session.config.getoption('self_contained_html')
        self._save_report(report_content, self_contained_html)

    def pytest_terminal_summary(self, terminalreporter):
        terminalreporter.write_sep('-', 'generated html file: {0}'.format(
            self.logfile))
