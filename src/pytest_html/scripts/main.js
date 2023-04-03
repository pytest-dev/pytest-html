const { formatDuration } = require('./utils.js')
const { dom, findAll } = require('./dom.js')
const { manager } = require('./datamanager.js')
const { doSort } = require('./sort.js')
const { doFilter } = require('./filter.js')
const { getVisible } = require('./storage.js')

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
    const renderSet = tests.filter(({ when, outcome }) => when === 'call' || outcome === 'Error' )
    const rows = renderSet.map(dom.getResultTBody)
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
    const renderSet = tests.filter(({ when, outcome }) => when === 'call' || outcome === 'Error')

    const possibleOutcomes = [
        { outcome: 'passed', label: 'Passed' },
        { outcome: 'skipped', label: 'Skipped' },
        { outcome: 'failed', label: 'Failed' },
        { outcome: 'error', label: 'Errors' },
        { outcome: 'xfailed', label: 'Unexpected failures' },
        { outcome: 'xpassed', label: 'Unexpected passes' },
        { outcome: 'rerun', label: 'Reruns' },
    ]

    const currentFilter = getVisible()
    possibleOutcomes.forEach(({ outcome, label }) => {
        const count = renderSet.filter((test) => test.outcome.toLowerCase() === outcome).length
        const input = document.querySelector(`input[data-test-result="${outcome}"]`)
        document.querySelector(`.${outcome}`).innerText = `${count} ${label}`

        input.disabled = !count
        input.checked = currentFilter.includes(outcome)
    })

    const numberOfTests = renderSet.filter(({ outcome }) =>
        ['Passed', 'Failed', 'XPassed', 'XFailed'].includes(outcome)).length

    if (isFinished) {
        const accTime = tests.reduce((prev, { duration }) => prev + duration, 0)
        const formattedAccTime = formatDuration(accTime)
        const testWord = numberOfTests > 1 ? 'tests' : 'test'
        const durationText = formattedAccTime.hasOwnProperty('ms') ? formattedAccTime.ms : formattedAccTime.seconds

        document.querySelector('.run-count').innerText = `${numberOfTests} ${testWord} ran in ${durationText}.`
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
