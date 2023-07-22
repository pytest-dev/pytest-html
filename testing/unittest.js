const { expect } = require('chai')
const sinon = require('sinon')
const { doInitFilter, doFilter } = require('../src/pytest_html/scripts/filter.js')
const { doInitSort, doSort } = require('../src/pytest_html/scripts/sort.js')
const dataModule = require('../src/pytest_html/scripts/datamanager.js')
const storageModule = require('../src/pytest_html/scripts/storage.js')


const setTestData = () => {
    const jsonDatan = {
        'tests':
            [
                {
                    'id': 'passed_1',
                    'result': 'passed',
                },
                {
                    'id': 'failed_2',
                    'result': 'failed',
                },
                {
                    'id': 'passed_3',
                    'result': 'passed',
                },
                {
                    'id': 'passed_4',
                    'result': 'passed',
                },
                {
                    'id': 'passed_5',
                    'result': 'passed',
                },
                {
                    'id': 'passed_6',
                    'result': 'passed',
                },
            ],
    }
    dataModule.manager.setManager(jsonDatan)
}

describe('Filter tests', () => {
    let getFilterMock
    let managerSpy

    beforeEach(setTestData)
    afterEach(() => [getFilterMock, managerSpy].forEach((fn) => fn.restore()))
    after(() => dataModule.manager.setManager({ tests: [] }))

    describe('doInitFilter', () => {
        it('has no stored filters', () => {
            getFilterMock = sinon.stub(storageModule, 'getVisible').returns([])
            managerSpy = sinon.spy(dataModule.manager, 'setRender')

            doInitFilter()
            expect(managerSpy.callCount).to.eql(1)
            expect(dataModule.manager.testSubset.map(({ result }) => result)).to.eql([])
        })
        it('exclude passed', () => {
            getFilterMock = sinon.stub(storageModule, 'getVisible').returns(['failed'])
            managerSpy = sinon.spy(dataModule.manager, 'setRender')

            doInitFilter()
            expect(managerSpy.callCount).to.eql(1)
            expect(dataModule.manager.testSubset.map(({ result }) => result)).to.eql(['failed'])
        })
    })
    describe('doFilter', () => {
        let setFilterMock
        afterEach(() => setFilterMock.restore())
        it('removes all but passed', () => {
            getFilterMock = sinon.stub(storageModule, 'getVisible').returns(['passed'])
            setFilterMock = sinon.stub(storageModule, 'setFilter')
            managerSpy = sinon.spy(dataModule.manager, 'setRender')

            doFilter('passed', true)
            expect(managerSpy.callCount).to.eql(1)
            expect(dataModule.manager.testSubset.map(({ result }) => result)).to.eql([
                'passed', 'passed', 'passed', 'passed', 'passed',
            ])
        })
    })
})


describe('Sort tests', () => {
    beforeEach(setTestData)
    after(() => dataModule.manager.setManager({ tests: [] }))
    describe('doInitSort', () => {
        let managerSpy
        let sortMock
        let sortDirectionMock
        beforeEach(() => dataModule.manager.resetRender())

        afterEach(() => [sortMock, sortDirectionMock, managerSpy].forEach((fn) => fn.restore()))
        it('has no stored sort', () => {
            sortMock = sinon.stub(storageModule, 'getSort').returns(null)
            sortDirectionMock = sinon.stub(storageModule, 'getSortDirection').returns(null)
            managerSpy = sinon.spy(dataModule.manager, 'setRender')

            doInitSort()
            expect(managerSpy.callCount).to.eql(1)
            expect(dataModule.manager.testSubset.map(({ result }) => result)).to.eql([
                'failed', 'passed', 'passed', 'passed', 'passed', 'passed',
            ])
        })
        it('has stored sort preference', () => {
            sortMock = sinon.stub(storageModule, 'getSort').returns('result')
            sortDirectionMock = sinon.stub(storageModule, 'getSortDirection').returns(false)
            managerSpy = sinon.spy(dataModule.manager, 'setRender')

            doInitSort()
            expect(managerSpy.callCount).to.eql(1)
            expect(dataModule.manager.testSubset.map(({ result }) => result)).to.eql([
                'failed', 'passed', 'passed', 'passed', 'passed', 'passed',
            ])
        })
        it('keeps original test execution order', () => {
            sortMock = sinon.stub(storageModule, 'getSort').returns('original')
            sortDirectionMock = sinon.stub(storageModule, 'getSortDirection').returns(false)
            managerSpy = sinon.spy(dataModule.manager, 'setRender')

            doInitSort()
            expect(managerSpy.callCount).to.eql(1)
            expect(dataModule.manager.testSubset.map(({ result }) => result)).to.eql([
                'passed', 'failed', 'passed', 'passed', 'passed', 'passed',
            ])
        })
    })
    describe('doSort', () => {
        let getSortMock
        let setSortMock
        let getSortDirectionMock
        let setSortDirection
        let managerSpy

        afterEach(() => [
            getSortMock, setSortMock, getSortDirectionMock, setSortDirection, managerSpy,
        ].forEach((fn) => fn.restore()))
        it('sort on result', () => {
            getSortMock = sinon.stub(storageModule, 'getSort').returns(null)
            setSortMock = sinon.stub(storageModule, 'setSort')
            getSortDirectionMock = sinon.stub(storageModule, 'getSortDirection').returns(null)
            setSortDirection = sinon.stub(storageModule, 'setSortDirection')
            managerSpy = sinon.spy(dataModule.manager, 'setRender')

            doSort('result')
            expect(managerSpy.callCount).to.eql(1)
            expect(dataModule.manager.testSubset.map(({ result }) => result)).to.eql([
                'passed', 'passed', 'passed', 'passed', 'passed', 'failed',
            ])
        })
    })
})

describe('Storage tests', () => {
    describe('getCollapsedCategory', () => {
        let originalWindow
        const mockWindow = (queryParam) => {
            const mock = {
                location: {
                    href: `https://example.com/page?${queryParam}`,
                },
            }
            originalWindow = global.window
            global.window = mock
        }
        after(() => global.window = originalWindow)

        it('collapses passed by default', () => {
            mockWindow()
            const collapsedItems = storageModule.getCollapsedCategory()
            expect(collapsedItems).to.eql(['passed'])
        })

        it('collapses specified outcomes', () => {
            mockWindow('collapsed=failed,error')
            const collapsedItems = storageModule.getCollapsedCategory()
            expect(collapsedItems).to.eql(['failed', 'error'])
        })

        it('collapses all', () => {
            mockWindow('collapsed=all')
            const collapsedItems = storageModule.getCollapsedCategory()
            expect(collapsedItems).to.eql(storageModule.possibleFilters)
        })

        it('handles case insensitive params', () => {
            mockWindow('collapsed=fAiLeD,ERROR,passed')
            const collapsedItems = storageModule.getCollapsedCategory()
            expect(collapsedItems).to.eql(['failed', 'error', 'passed'])
        })

        const config = [
            { value: ['failed', 'error'], expected: ['failed', 'error'] },
            { value: ['all'], expected: storageModule.possibleFilters },
        ]
        config.forEach(({ value, expected }) => {
            it(`handles python config: ${value}`, () => {
                mockWindow()
                const collapsedItems = storageModule.getCollapsedCategory(value)
                expect(collapsedItems).to.eql(expected)
            })
        })

        const precedence = [
            { query: 'collapsed=xpassed,xfailed', value: ['failed', 'error'], expected: ['xpassed', 'xfailed'] },
            { query: 'collapsed=all', value: ['failed', 'error'], expected: storageModule.possibleFilters },
            { query: 'collapsed=xpassed,xfailed', value: ['all'], expected: ['xpassed', 'xfailed'] },
        ]
        precedence.forEach(({ query, value, expected }, index) => {
            it(`handles python config precedence ${index + 1}`, () => {
                mockWindow(query)
                const collapsedItems = storageModule.getCollapsedCategory(value)
                expect(collapsedItems).to.eql(expected)
            })
        })

        const falsy = [
            { param: 'collapsed' },
            { param: 'collapsed=' },
            { param: 'collapsed=""' },
            { param: 'collapsed=\'\'' },
        ]
        falsy.forEach(({ param }) => {
            it(`collapses none with ${param}`, () => {
                mockWindow(param)
                const collapsedItems = storageModule.getCollapsedCategory()
                expect(collapsedItems).to.be.empty
            })
        })
    })
})
