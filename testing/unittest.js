const { expect } = require('chai')
const sinon = require('sinon')
const { doInitFilter, doFilter } = require('../src/pytest_html/scripts/filter.js')
const { doInitSort, doSort } = require('../src/pytest_html/scripts/sort.js')
const dataModule = require('../src/pytest_html/scripts/datamanager.js')
const storageModule = require('../src/pytest_html/scripts/storage.js')


describe('Filter tests', () => {
    let getFilterMock
    let managerSpy
    before(() => {
        const jsonDatan = {
            'tests':
                [
                    {
                        'id': 'passed_1',
                        'outcome': 'passed',
                    },
                    {
                        'id': 'failed_2',
                        'outcome': 'failed',
                    },
                    {
                        'id': 'passed_3',
                        'outcome': 'passed',
                    },
                    {
                        'id': 'passed_4',
                        'outcome': 'passed',
                    },
                    {
                        'id': 'passed_5',
                        'outcome': 'passed',
                    },
                    {
                        'id': 'passed_6',
                        'outcome': 'passed',
                    },
                ],
        }
        dataModule.manager.setManager(jsonDatan)
    })
    afterEach(() => [getFilterMock, managerSpy].forEach((fn) => fn.restore()))
    after(() => dataModule.manager.setManager({ tests: [] }))
    describe('doInitFilter', () => {
        it('has no stored filters', () => {
            getFilterMock = sinon.stub(storageModule, 'getFilter').returns([])
            managerSpy = sinon.spy(dataModule.manager, 'setRender')

            doInitFilter()
            expect(managerSpy.callCount).to.eql(1)
            expect(dataModule.manager.testSubset.map(({ outcome }) => outcome)).to.eql([
                'passed', 'failed', 'passed', 'passed', 'passed', 'passed',
            ])
        })
        it('exclude passed', () => {
            getFilterMock = sinon.stub(storageModule, 'getFilter').returns(['passed'])
            managerSpy = sinon.spy(dataModule.manager, 'setRender')

            doInitFilter()
            expect(managerSpy.callCount).to.eql(1)
            expect(dataModule.manager.testSubset.map(({ outcome }) => outcome)).to.eql(['failed'])
        })
    })
    describe('doFilter', () => {
        let setFilterMock
        afterEach(() => setFilterMock.restore())
        it('removes a filter', () => {
            getFilterMock = sinon.stub(storageModule, 'getFilter').returns(['passed'])
            setFilterMock = sinon.stub(storageModule, 'setFilter')
            managerSpy = sinon.spy(dataModule.manager, 'setRender')

            doFilter('passed', true)
            expect(managerSpy.callCount).to.eql(0)
            expect(dataModule.manager.testSubset.map(({ outcome }) => outcome)).to.eql([
                'passed', 'failed', 'passed', 'passed', 'passed', 'passed'
            ])
        })
        it('applies a filter', () => {
            getFilterMock = sinon.stub(storageModule, 'getFilter').returns([])
            setFilterMock = sinon.stub(storageModule, 'setFilter')
            managerSpy = sinon.spy(dataModule.manager, 'setRender')

            doFilter('passed', false)
            expect(managerSpy.callCount).to.eql(1)
            expect(dataModule.manager.testSubset.map(({outcome}) => outcome)).to.eql([ 'failed' ])
        })
    })
})


describe('Sort tests', () => {
    before(() => {
        const jsonDatan = {
            'tests': 
                [
                    {
                        'id': 'outcome_1',
                        'outcome': 'passed',
                    },
                    {
                        'id': 'outcome_2',
                        'outcome': 'failed',
                    },
                    {
                        'id': 'outcome_3',
                        'outcome': 'passed',
                    },
                    {
                        'id': 'outcome_4',
                        'outcome': 'passed',
                    },
                    {
                        'id': 'outcome_5',
                        'outcome': 'passed',
                    },
                    {
                        'id': 'outcome_6',
                        'outcome': 'passed',
                    },
                ],
        }
        dataModule.manager.setManager(jsonDatan)
    })
    after(() => dataModule.manager.setManager({ tests: [] }))
    describe('doInitSort', () => {
        let managerSpy
        let sortMock
        let sortDirectionMock
        beforeEach(() => dataModule.manager.resetRender())

        afterEach(() => [sortMock,sortDirectionMock, managerSpy].forEach((fn) => fn.restore()))
        it('has no stored sort', () => {
            sortMock = sinon.stub(storageModule, 'getSort').returns(null)
            sortDirectionMock = sinon.stub(storageModule, 'getSortDirection').returns(null)
            managerSpy = sinon.spy(dataModule.manager, 'setRender')

            doInitSort()
            expect(managerSpy.callCount).to.eql(1)
            expect(dataModule.manager.testSubset.map(({ outcome }) => outcome)).to.eql([
                'passed', 'failed', 'passed', 'passed', 'passed', 'passed',
            ])
        })
        it('has stored sort preference', () => {
            sortMock = sinon.stub(storageModule, 'getSort').returns('outcome')
            sortDirectionMock = sinon.stub(storageModule, 'getSortDirection').returns(false)
            managerSpy = sinon.spy(dataModule.manager, 'setRender')

            doInitSort()
            expect(managerSpy.callCount).to.eql(1)
            expect(dataModule.manager.testSubset.map(({ outcome }) => outcome)).to.eql([
                'failed', 'passed', 'passed', 'passed', 'passed', 'passed',
            ])
        })
    })
    describe('doSort', () => {
        let getSortMock, setSortMock, getSortDirectionMock, setSortDirection, managerSpy

        afterEach(() => [getSortMock, setSortMock, getSortDirectionMock, setSortDirection, managerSpy].forEach(fn => fn.restore()))
        it('sort on outcome', () => {
            getSortMock = sinon.stub(storageModule, 'getSort').returns(null)
            setSortMock = sinon.stub(storageModule, 'setSort')
            getSortDirectionMock = sinon.stub(storageModule, 'getSortDirection').returns(null)
            setSortDirection = sinon.stub(storageModule, 'setSortDirection')
            managerSpy = sinon.spy(dataModule.manager, 'setRender')

            doSort('outcome')
            expect(managerSpy.callCount).to.eql(1)
            expect(dataModule.manager.testSubset.map(({outcome}) => outcome)).to.eql([ 'passed', 'passed', 'passed', 'passed', 'passed', 'failed' ])
        })
    })
})
