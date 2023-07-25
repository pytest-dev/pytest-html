const { dom, findAll } = require('./dom.js')
const { manager } = require('./datamanager.js')
const { doSort } = require('./sort.js')
const { doFilter } = require('./filter.js')
const { getVisible, getSort, getSortDirection, possibleFilters } = require('./storage.js')

const removeChildren = (node) => {
    while (node.firstChild) {
        node.removeChild(node.firstChild)
    }
}

const renderStatic = () => {
    const renderEnvironmentTable = () => {
        const environment = manager.environment
        const rows = Object.keys(environment).map((key) => dom.getStaticRow(key, environment[key]))
        const table = document.getElementById('environment')
        removeChildren(table)
        rows.forEach((row) => table.appendChild(row))
    }
    renderEnvironmentTable()
}

const renderContent = (tests) => {
    const sortAttr = getSort(manager.allData.initialSort)
    const sortAsc = JSON.parse(getSortDirection())
    const rows = tests.map(dom.getResultTBody)
    const table = document.getElementById('results-table')
    const tableHeader = document.getElementById('template_results-table__head').content.cloneNode(true)

    removeChildren(table)

    tableHeader.querySelector(`.sortable[data-column-type="${sortAttr}"]`)?.classList.add(sortAsc ? 'desc' : 'asc')
    if (!rows.length) {
        tableHeader.appendChild(dom.getListHeaderEmpty())
    }
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

    findAll('.collapsible td:not(.col-links').forEach((elem) => {
        elem.addEventListener('click', ({ target }) => {
            manager.toggleCollapsedItem(target.parentElement.dataset.id)
            redraw()
        })
    })
}

const renderDerived = () => {
    const currentFilter = getVisible()
    possibleFilters.forEach((result) => {
        const input = document.querySelector(`input[data-test-result="${result}"]`)
        input.checked = currentFilter.includes(result)
    })
}

const bindEvents = () => {
    const filterColumn = (evt) => {
        const { target: element } = evt
        const { testResult } = element.dataset

        doFilter(testResult, element.checked)
        redraw()
    }

    const header = document.getElementById('environment-header')
    header.addEventListener('click', () => {
        const table = document.getElementById('environment')
        table.classList.toggle('hidden')
        header.classList.toggle('collapser')
        header.classList.toggle('expander')
    })

    findAll('input[name="filter_checkbox"]').forEach((elem) => {
        elem.addEventListener('click', filterColumn)
    })
    document.getElementById('show_all_details').addEventListener('click', () => {
        manager.allCollapsed = false
        redraw()
    })
    document.getElementById('hide_all_details').addEventListener('click', () => {
        manager.allCollapsed = true
        redraw()
    })
}

const redraw = () => {
    const { testSubset } = manager

    renderContent(testSubset)
    renderDerived()
}

module.exports = {
    redraw,
    bindEvents,
    renderStatic,
}
