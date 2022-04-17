const { expect } = require('chai')
const sinon = require('sinon')
const { doInitFilter, doFilter } = require('../src/pytest_html/scripts/filter.js')
const { doInitSort, doSort } = require('../src/pytest_html/scripts/sort.js')
const dataModule = require('../src/pytest_html/scripts/datamanager.js')
const localStorageModule = require('../src/pytest_html/scripts/localstorage_utils.js')


describe('Filter tests', function () {
    let getFilterMock, managerSpy
    beforeEach(() => dataModule.manager.resetRender())
    this.afterEach(() => [getFilterMock, managerSpy].forEach( fn => fn.restore()))
    describe('doInitFilter', () =>  {
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