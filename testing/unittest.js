const { expect } = require('chai')
const sinon = require('sinon')
const { doInitFilter, doFilter } = require('../src/pytest_html/scripts/filter.js')
const { doInitSort, doSort } = require('../src/pytest_html/scripts/sort.js')
const dataModule = require('../src/pytest_html/scripts/datamanager.js')
const localStorageModule = require('../src/pytest_html/scripts/localstorage_utils.js')

const jsonData = {"title": "REAL REPORT", "collectedItems": 2, "environment": {"Python": "3.9.10", "Platform": "macOS-11.6-x86_64-i386-64bit", "Packages": {"pytest": "6.2.5", "py": "1.11.0", "pluggy": "1.0.0"}, "Plugins": {"metadata": "1.11.0", "html": "3.1.2.dev69"}}, "tests": [{"nodeid": "test_html.py::test_url", "location": ["test_html.py", 4, "test_url"], "keywords": {"test_url": 1, "test_html.py": 1, "testing-html": 1}, "outcome": "passed", "longrepr": null, "when": "setup", "user_properties": [], "sections": [], "duration": 0.0003443180000000101, "$report_type": "TestReport"}, {"nodeid": "test_html.py::test_url", "location": ["test_html.py", 4, "test_url"], "keywords": {"test_url": 1, "test_html.py": 1, "testing-html": 1}, "outcome": "failed", "longrepr": {"reprcrash": {"path": "/Volumes/code/testing-html/test_html.py", "lineno": 16, "message": "assert False"}, "reprtraceback": {"reprentries": [{"type": "ReprEntry", "data": {"lines": ["    def test_url(extra):", "        \"\"\"", "            meh", "            alb alb alb", "            @param: hello", "            :param just", "        \"\"\"", "        # driver.get(\"https://www.google.com\")", "        extra.append(extras.text(\"some string\"))", "        extra.append(extras.image(\"file:///Users/jimbrannlund/dev/pytest-dev/testing-html/screenshot.png\"))", "        extra.append(extras.image(\"file:///Users/jimbrannlund/dev/pytest-dev/testing-html/screenshot.png\"))", ">       assert False", "E       assert False"], "reprfuncargs": {"args": [["extra", "[{'content': 'some string', 'extension': 'txt', 'format_type': 'text', 'mime_type': 'text/plain', ...}, {'content': 'f...ev/pytest-dev/testing-html/screenshot.png', 'extension': 'png', 'format_type': 'image', 'mime_type': 'image/png', ...}]"]]}, "reprlocals": null, "reprfileloc": {"path": "test_html.py", "lineno": 16, "message": "AssertionError"}, "style": "long"}}], "extraline": null, "style": "long"}, "sections": [], "chain": [[{"reprentries": [{"type": "ReprEntry", "data": {"lines": ["    def test_url(extra):", "        \"\"\"", "            bla bla bla bla", "            alb alb alb", "            @param: hello", "            :param just", "        \"\"\"", "        # driver.get(\"https://www.google.com\")", "        extra.append(extras.text(\"some string\"))", "        extra.append(extras.image(\"file:///Users/jimbrannlund/dev/pytest-dev/testing-html/screenshot.png\"))", "        extra.append(extras.image(\"file:///Users/jimbrannlund/dev/pytest-dev/testing-html/screenshot.png\"))", ">       assert False", "E       assert False"], "reprfuncargs": {"args": [["extra", "[{'content': 'some string', 'extension': 'txt', 'format_type': 'text', 'mime_type': 'text/plain', ...}, {'content': 'f...ev/pytest-dev/testing-html/screenshot.png', 'extension': 'png', 'format_type': 'image', 'mime_type': 'image/png', ...}]"]]}, "reprlocals": null, "reprfileloc": {"path": "test_html.py", "lineno": 16, "message": "AssertionError"}, "style": "long"}}], "extraline": null, "style": "long"}, {"path": "/Volumes/code/testing-html/test_html.py", "lineno": 16, "message": "assert False"}, null]]}, "when": "call", "user_properties": [], "sections": [], "duration": 0.00022838299999999867, "extra": [{"name": "Text", "format_type": "text", "content": "some string", "mime_type": "text/plain", "extension": "txt"}, {"name": "Image", "format_type": "image", "content": "file:///Users/jimbrannlund/dev/pytest-dev/testing-html/screenshot.png", "mime_type": "image/png", "extension": "png"}, {"name": "Image", "format_type": "image", "content": "file:///Users/jimbrannlund/dev/pytest-dev/testing-html/screenshot.png", "mime_type": "image/png", "extension": "png"}], "$report_type": "TestReport"}, {"nodeid": "test_html.py::test_url", "location": ["test_html.py", 4, "test_url"], "keywords": {"test_url": 1, "test_html.py": 1, "testing-html": 1}, "outcome": "passed", "longrepr": null, "when": "teardown", "user_properties": [], "sections": [], "duration": 0.00014628500000002376, "$report_type": "TestReport"}, {"nodeid": "test_html.py::test_url2", "location": ["test_html.py", 18, "test_url2"], "keywords": {"test_html.py": 1, "test_url2": 1, "testing-html": 1}, "outcome": "passed", "longrepr": null, "when": "setup", "user_properties": [], "sections": [], "duration": 0.00011052099999997456, "$report_type": "TestReport"}, {"nodeid": "test_html.py::test_url2", "location": ["test_html.py", 18, "test_url2"], "keywords": {"test_html.py": 1, "test_url2": 1, "testing-html": 1}, "outcome": "passed", "longrepr": null, "when": "call", "user_properties": [], "sections": [], "duration": 0.0001266319999999599, "extra": [], "$report_type": "TestReport"}, {"nodeid": "test_html.py::test_url2", "location": ["test_html.py", 18, "test_url2"], "keywords": {"test_html.py": 1, "test_url2": 1, "testing-html": 1}, "outcome": "passed", "longrepr": null, "when": "teardown", "user_properties": [], "sections": [], "duration": 0.0002340050000000371, "$report_type": "TestReport"}]}

describe('Filter tests', function () {
    let getFilterMock, managerSpy

    this.afterEach(() => [getFilterMock, managerSpy].forEach( fn => fn.restore()))
    describe('doInitFilter', function() {
        before(function() {
            dataModule.manager.setManager(jsonData)
        })

        it("has no stored filters", () => {
            getFilterMock = sinon.stub(localStorageModule, 'getFilter').returns([])
            managerSpy = sinon.spy(dataModule.manager, 'setRender')

            doInitFilter()
            expect(managerSpy.callCount).to.eql(1)
            expect(dataModule.manager.getRender().map(({outcome}) => outcome)).to.eql([ 'passed', 'failed', 'passed', 'passed', 'passed', 'passed' ])
        })
        it("exclude passed", () => {
            getFilterMock = sinon.stub(localStorageModule, 'getFilter').returns(['passed'])
            managerSpy = sinon.spy(dataModule.manager, 'setRender')

            doInitFilter()
            expect(managerSpy.callCount).to.eql(1)
            expect(dataModule.manager.getRender().map(({outcome}) => outcome)).to.eql([ 'failed' ])
        })
    })
    describe('doFilter', () => {
        var setFilterMock
        afterEach(() => setFilterMock.restore())
        it("removes a filter", () => {
            getFilterMock = sinon.stub(localStorageModule, 'getFilter').returns(['passed'])
            setFilterMock = sinon.stub(localStorageModule, 'setFilter')
            managerSpy = sinon.spy(dataModule.manager, 'setRender')

            doFilter('passed', true)
            expect(managerSpy.callCount).to.eql(0)
            expect(dataModule.manager.getRender().map(({outcome}) => outcome)).to.eql([ 'passed', 'failed', 'passed', 'passed', 'passed', 'passed' ])
        })
        it("applies a filter", () => {
            getFilterMock = sinon.stub(localStorageModule, 'getFilter').returns([])
            setFilterMock = sinon.stub(localStorageModule, 'setFilter')
            managerSpy = sinon.spy(dataModule.manager, 'setRender')

            doFilter('passed', false)
            expect(managerSpy.callCount).to.eql(1)
            expect(dataModule.manager.getRender().map(({outcome}) => outcome)).to.eql([ 'failed' ])
        })
    })
})


describe('Sort tests', () => {
    describe('doInitSort', () =>  {
        let managerSpy, sortMock, sortDirectionMock
        beforeEach(() => dataModule.manager.resetRender())

        afterEach(() => [sortMock,sortDirectionMock,managerSpy].forEach(fn => fn.restore()))
        it("has no stored sort", () => {
            sortMock = sinon.stub(localStorageModule, 'getSort').returns(null)
            sortDirectionMock = sinon.stub(localStorageModule, 'getSortDirection').returns(null)
            managerSpy = sinon.spy(dataModule.manager, 'setRender')

            doInitSort()
            expect(managerSpy.callCount).to.eql(1)
            expect(dataModule.manager.getRender().map(({outcome}) => outcome)).to.eql([ 'passed', 'failed', 'passed', 'passed', 'passed', 'passed' ])
        })
        it("has stored sort preference", () => {
            sortMock = sinon.stub(localStorageModule, 'getSort').returns('outcome')
            sortDirectionMock = sinon.stub(localStorageModule, 'getSortDirection').returns(false)
            managerSpy = sinon.spy(dataModule.manager, 'setRender')

            doInitSort()
            expect(managerSpy.callCount).to.eql(1)
            expect(dataModule.manager.getRender().map(({outcome}) => outcome)).to.eql([ 'failed', 'passed', 'passed', 'passed', 'passed', 'passed' ])
        })
    })
    describe('doSort', () => {
        let getSortMock, setSortMock, getSortDirectionMock, setSortDirection, managerSpy

        afterEach(() => [getSortMock, setSortMock, getSortDirectionMock, setSortDirection, managerSpy].forEach(fn => fn.restore()))
        it("sort on outcome", () => {
            getSortMock = sinon.stub(localStorageModule, 'getSort').returns(null)
            setSortMock = sinon.stub(localStorageModule, 'setSort')
            getSortDirectionMock = sinon.stub(localStorageModule, 'getSortDirection').returns(null)
            setSortDirection = sinon.stub(localStorageModule, 'setSortDirection')
            managerSpy = sinon.spy(dataModule.manager, 'setRender')

            doSort('outcome')
            expect(managerSpy.callCount).to.eql(1)
            expect(dataModule.manager.getRender().map(({outcome}) => outcome)).to.eql([ 'passed', 'passed', 'passed', 'passed', 'passed', 'failed' ])
        })
    })
})
