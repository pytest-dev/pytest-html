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


def pytest_configure(config):
    config._environment = []
    htmlpath = config.option.htmlpath
    # prevent opening htmlpath on slave nodes (xdist)
    if htmlpath and not hasattr(config, 'slaveinput'):
        config._html = HTMLReport(htmlpath)
        config.pluginmanager.register(config._html)
    if hasattr(config, 'slaveoutput'):
        config.slaveoutput['environment'] = config._environment


@pytest.mark.optionalhook
def pytest_testnodedown(node):
    # note that any environments from remote slaves will be replaced with the
    # environment from the final slave to quit
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

    def __init__(self, logfile):
        logfile = os.path.expanduser(os.path.expandvars(logfile))
        self.logfile = os.path.abspath(logfile)
        self.test_logs = []
        self.errors = self.failed = 0
        self.passed = self.skipped = 0
        self.xfailed = self.xpassed = 0

    def _appendrow(self, result, report):
        time = getattr(report, 'duration', 0.0)

        additional_html = []
        links_html = []

        for extra in getattr(report, 'extra', []):
            href = None
            if extra.get('format') == extras.FORMAT_IMAGE:
                href = '#'
                image = 'data:image/png;base64,{0}'.format(
                    extra.get('content'))
                additional_html.append(html.div(
                    html.a(html.img(src=image), href="#"),
                    class_='image'))
            elif extra.get('format') == extras.FORMAT_HTML:
                additional_html.append(extra.get('content'))
            elif extra.get('format') == extras.FORMAT_JSON:
                href = data_uri(json.dumps(extra.get('content')),
                                mime_type='application/json')
            elif extra.get('format') == extras.FORMAT_TEXT:
                href = data_uri(extra.get('content'))
            elif extra.get('format') == extras.FORMAT_URL:
                href = extra.get('content')

            if href is not None:
                links_html.append(html.a(
                    extra.get('name'),
                    class_=extra.get('format'),
                    href=href,
                    target='_blank'))
                links_html.append(' ')

        if report.longrepr:
            log = html.div(class_='log')
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
        else:
            log = html.div(class_='empty log')
            log.append('No log output captured.')
        additional_html.append(log)

        self.test_logs.append(html.tr([
            html.td(result, class_='col-result'),
            html.td(report.nodeid, class_='col-name'),
            html.td('{0:.2f}'.format(time), class_='col-duration'),
            html.td(links_html, class_='col-links'),
            html.td(additional_html, class_='extra')],
            class_=result.lower() + ' results-table-row'))

    def append_pass(self, report):
        self.passed += 1
        self._appendrow('Passed', report)

    def append_failure(self, report):
        if hasattr(report, "wasxfail"):
            self._appendrow('XPassed', report)
            self.xpassed += 1
        else:
            self._appendrow('Failed', report)
            self.failed += 1

    def append_error(self, report):
        self._appendrow('Error', report)
        self.errors += 1

    def append_skipped(self, report):
        if hasattr(report, "wasxfail"):
            self._appendrow('XFailed', report)
            self.xfailed += 1
        else:
            self._appendrow('Skipped', report)
            self.skipped += 1

    def pytest_runtest_logreport(self, report):
        if report.passed:
            if report.when == 'call':
                self.append_pass(report)
        elif report.failed:
            if report.when != "call":
                self.append_error(report)
            else:
                self.append_failure(report)
        elif report.skipped:
            self.append_skipped(report)

    def pytest_sessionstart(self, session):
        self.suite_start_time = time.time()

    def pytest_sessionfinish(self, session):
        if not os.path.exists(os.path.dirname(self.logfile)):
            os.makedirs(os.path.dirname(self.logfile))
        logfile = open(self.logfile, 'w', encoding='utf-8')
        suite_stop_time = time.time()
        suite_time_delta = suite_stop_time - self.suite_start_time
        numtests = self.passed + self.failed + self.xpassed + self.xfailed
        generated = datetime.datetime.now()

        style_css = pkg_resources.resource_string(
            __name__, os.path.join('resources', 'style.css'))
        if PY3:
            style_css = style_css.decode('utf-8')

        head = html.head(
            html.meta(charset='utf-8'),
            html.title('Test Report'),
            html.style(raw(style_css)))

        summary = [html.h2('Summary'), html.p(
            '{0} tests ran in {1:.2f} seconds.'.format(
                numtests, suite_time_delta),
            html.br(),
            html.span('{0} passed'.format(
                self.passed), class_='passed'), ', ',
            html.span('{0} skipped'.format(
                self.skipped), class_='skipped'), ', ',
            html.span('{0} failed'.format(
                self.failed), class_='failed'), ', ',
            html.span('{0} errors'.format(
                self.errors), class_='error'), '.',
            html.br(),
            html.span('{0} expected failures'.format(
                self.xfailed), class_='skipped'), ', ',
            html.span('{0} unexpected passes'.format(
                self.xpassed), class_='failed'), '.')]

        results = [html.h2('Results'), html.table([html.thead(
            html.tr([
                html.th('Result',
                        class_='sortable initial-sort result',
                        col='result'),
                html.th('Test', class_='sortable', col='name'),
                html.th('Duration',
                        class_='sortable numeric',
                        col='duration'),
                html.th('Links')]), id='results-table-head'),
            html.tbody(*self.test_logs, id='results-table-body')],
            id='results-table')]

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
            body.append(html.h2('Environment'))
            body.append(html.table(
                [html.tr(html.td(e[0]), html.td(e[1])) for e in sorted(
                    session.config._environment, key=lambda e: e[0]) if e[1]],
                id='environment'))

        body.extend(summary)
        body.extend(results)

        doc = html.html(head, body)

        logfile.write('<!DOCTYPE html>')
        unicode_doc = doc.unicode(indent=2)
        if PY3:
            # Fix encoding issues, e.g. with surrogates
            unicode_doc = unicode_doc.encode('utf-8',
                                             errors='xmlcharrefreplace')
            unicode_doc = unicode_doc.decode('utf-8')
        logfile.write(unicode_doc)
        logfile.close()

    def pytest_terminal_summary(self, terminalreporter):
        terminalreporter.write_sep('-', 'generated html file: {0}'.format(
            self.logfile))
