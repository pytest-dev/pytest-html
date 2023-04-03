const { formatDuration } = require('./utils.js')
const { dom, findAll } = require('./dom.js')
const { manager } = require('./datamanager.js')
const { doSort } = require('./sort.js')
const { doFilter } = require('./filter.js')
const { getVisible, possibleResults } = require('./storage.js')

const removeChildren = (node) => {
    while (node.firstChild) {
        node.removeChild(node.firstChild)
    }
}

const renderStatic = () => {
    const renderTitle = () => {
        const title = manager.title
        document.querySelector('#title').innerText = title
        document.querySelector('#head-title').innerText = title
    }
    const renderTable = () => {
        const environment = manager.environment
        const rows = Object.keys(environment).map((key) => dom.getStaticRow(key, environment[key]))
        const table = document.querySelector('#environment')
        removeChildren(table)
        rows.forEach((row) => table.appendChild(row))
    }
    renderTitle()
    renderTable()
}

const renderContent = (tests) => {
    const rows = tests.map(dom.getResultTBody)
    const table = document.querySelector('#results-table')
    removeChildren(table)
    const tableHeader = dom.getListHeader(manager.renderData)
    if (!rows.length) {
        tableHeader.appendChild(dom.getListHeaderEmpty())
    }
    table.appendChild(dom.getColGroup())
    table.appendChild(tableHeader)

    rows.forEach((row) => !!row && table.appendChild(row))

    table.querySelectorAll('.extra').forEach((item) => {
        item.colSpan = document.querySelectorAll('th').length
    })
    findAll('.sortable').forEach((elem) => {
        elem.addEventListener('click', (evt) => {
            const { target: element } = evt
            const { columnType } = element.dataset
            doSort(columnType)
            redraw()
        })
    })
    findAll('.col-result').forEach((elem) => {
        elem.addEventListener('click', ({ target }) => {
            manager.toggleCollapsedItem(target.dataset.id)
            redraw()
        })
    })
}

const renderDerived = (tests, collectedItems, isFinished) => {
    const currentFilter = getVisible()
    possibleResults.forEach(({ result, label }) => {
        const count = tests.filter((test) => test.result.toLowerCase() === result).length
        const input = document.querySelector(`input[data-test-result="${result}"]`)
        document.querySelector(`.${result}`).innerText = `${count} ${label}`

        input.disabled = !count
        input.checked = currentFilter.includes(result)
    })

    const numberOfTests = tests.filter(({ result }) =>
        ['Passed', 'Failed', 'XPassed', 'XFailed'].includes(result)).length

    if (isFinished) {
        const accTime = tests.reduce((prev, { duration }) => prev + duration, 0)
        const formattedAccTime = formatDuration(accTime)
        const testWord = numberOfTests > 1 ? 'tests' : 'test'
        const durationText = formattedAccTime.hasOwnProperty('ms') ? formattedAccTime.ms : formattedAccTime.formatted

        document.querySelector('.run-count').innerText = `${numberOfTests} ${testWord} took ${durationText}.`
        document.querySelector('.summary__reload__button').classList.add('hidden')
    } else {
        document.querySelector('.run-count').innerText = `${numberOfTests} / ${collectedItems} tests done`
    }
}

const bindEvents = () => {
    const filterColumn = (evt) => {
        const { target: element } = evt
        const { testResult } = element.dataset

        doFilter(testResult, element.checked)
        redraw()
    }
    findAll('input[name="filter_checkbox"]').forEach((elem) => {
        elem.removeEventListener('click', filterColumn)
        elem.addEventListener('click', filterColumn)
    })
    document.querySelector('#show_all_details').addEventListener('click', () => {
        manager.allCollapsed = false
        redraw()
    })
    document.querySelector('#hide_all_details').addEventListener('click', () => {
        manager.allCollapsed = true
        redraw()
    })
}

const redraw = () => {
    const { testSubset, allTests, collectedItems, isFinished } = manager

    renderStatic()
    renderContent(testSubset)
    renderDerived(allTests, collectedItems, isFinished)
}

exports.redraw = redraw
exports.bindEvents = bindEvents
