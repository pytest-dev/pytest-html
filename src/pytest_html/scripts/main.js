const { formatDuration } = require('./utils.js')
const { dom, findAll } = require('./dom.js')
const { manager } = require('./datamanager.js')
const { doSort } = require('./sort.js')
const { doFilter } = require('./filter.js')
const { getFilter } = require('./localstorage_utils.js')

const removeChildren = (node) => {
    while (node.firstChild) {
        node.removeChild(node.firstChild)
    }
}

const renderStatic = () => {
    const title = manager.title
    const environment = manager.environment
    document.querySelector('#title').innerText = title
    document.querySelector('#head-title').innerText = title
    const rows = Object.keys(environment).map((key) =>
        dom.getStaticRow(key, environment[key])
    )

    const table = document.querySelector('#environment')
    removeChildren(table)
    rows.forEach((row) => table.appendChild(row))
}

const renderContent = (tests) => {
    const renderSet = tests.filter(({ when, outcome }) => when === 'call' || outcome === 'Error' )

    const rows = renderSet.map((test) =>
      dom.getResultTBody(test)
    )

    const table = document.querySelector('#results-table')
    removeChildren(table)
    const tableHeader = dom.getListHeader(manager.renderData)
    if (!rows.length) {
        tableHeader.appendChild(dom.getListHeaderEmpty())
    }

    table.appendChild(tableHeader)

    rows.forEach((row) => !!row && table.appendChild(row))

    table.querySelectorAll('.extra').forEach((item) => {
        item.colSpan = document.querySelectorAll('th').length
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

    const currentFilter = getFilter()
    possibleOutcomes.forEach(({ outcome, label }) => {
        const count = renderSet.filter((test) => test.outcome.toLowerCase() === outcome).length
        const input = document.querySelector(`input[data-test-result="${outcome}"]`)
        document.querySelector(`.${outcome}`).innerText = `${count} ${label}`

        input.disabled = !count
        input.checked = !currentFilter.includes(outcome)
    })

    const numberOfTests = renderSet.filter(({outcome}) =>
      ['Passed', 'Failed', 'XPassed', 'XFailed'].includes(outcome)
    ).length
    if (isFinished) {
        const accTime = tests.reduce((prev, { duration }) => prev + duration, 0)
        const formattedAccTime = formatDuration(accTime)
        const testWord = numberOfTests > 1 ? 'tests' : 'test'
        const innerText = `${numberOfTests} ${testWord} ran in ${formattedAccTime} seconds.`
        document.querySelector('.run-count').innerText = innerText
        document.querySelector('.summary__reload__button').classList.add('hidden')
    } else {
        document.querySelector('.run-count').innerText = `${numberOfTests} / ${collectedItems} tests done`
    }
}

const bindEvents = () => {
    findAll('.sortable').forEach((elem) => {
        elem.addEventListener('click', (evt) => {
            const { target: element } = evt
            const { columnType } = element.dataset

            doSort(columnType)
            redraw()
        })
    })
    findAll('input[name="filter_checkbox"]').forEach((elem) => {
        elem.addEventListener('click', (evt) => {
            const { target: element } = evt
            const { testResult } = element.dataset

            doFilter(testResult, element.checked)
            redraw()
        })
    })
}

const renderPage = () => {
    const { testSubset, allTests, collectedItems, isFinished } = manager

    renderStatic()
    renderContent(testSubset)
    renderDerived(allTests, collectedItems, isFinished)
}

const redraw = () => {
    setTimeout(() => {
        renderPage()
        bindEvents()
    }, 0)
}

exports.redraw = redraw
