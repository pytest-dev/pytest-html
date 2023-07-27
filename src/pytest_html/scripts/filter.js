const { manager } = require('./datamanager.js')
const storageModule = require('./storage.js')

const getFilteredSubSet = (filter) =>
    manager.testSubset.filter(({ result }) => filter.includes(result.toLowerCase()))

const doInitFilter = () => {
    const currentFilter = storageModule.getVisible()
    const resultsTable = document.getElementById('results-table')
    storageModule.possibleFilters.forEach(result => {
        const rows = resultsTable.getElementsByClassName(`results-table-row ${result}`)
        const rowsToShow = currentFilter.includes(result) ? rows : []
        const rowsToHide = currentFilter.includes(result) ? [] : rows

        for (const elementToShow of rowsToShow) {
            elementToShow.classList.remove('hidden')
        }

        for (const elementToHide of rowsToHide) {
            elementToHide.classList.add('hidden')
        }
    })
//    const filteredSubset = getFilteredSubSet(currentFilter)
//    manager.setRender(filteredSubset)
}

const doFilter = (type, show) => {
    if (show) {
        storageModule.showCategory(type)
    } else {
        storageModule.hideCategory(type)
    }

    const currentFilter = storageModule.getVisible()
    const resultsTable = document.getElementById('results-table')
    storageModule.possibleFilters.forEach(result => {
        const rows = resultsTable.getElementsByClassName(`results-table-row ${result}`)
        const rowsToShow = currentFilter.includes(result) ? rows : []
        const rowsToHide = currentFilter.includes(result) ? [] : rows

        for (const elementToShow of rowsToShow) {
            elementToShow.classList.remove('hidden')
        }

        for (const elementToHide of rowsToHide) {
            elementToHide.classList.add('hidden')
        }
    })

//    storageModule.possibleFilters.forEach(result => {
//        const rows = document.getElementById('results-table').getElementsByClassName(`results-table-row ${result}`)
//        if (currentFilter.includes(result)) {
//            Array.from(rows).forEach(element => {
//              element.classList.remove('hidden')
//            })
//        } else {
//            Array.from(rows).forEach(element => {
//              element.classList.add('hidden')
//            })
//        }
//    })
//    const diff = storageModule.possibleFilters.filter(item => !currentFilter.includes(item))
//    diff.forEach(result => {
//        document.getElementById('results-table').getElementsByClassName(`results-table-row ${result}`)
//    })
//    const filteredSubset = getFilteredSubSet(currentFilter)
//    console.log("filtered subset:")
//    console.log(filteredSubset)
//    console.log("test subset:")
//    console.log(manager.testSubset)
//    manager.setRender(filteredSubset)
}

module.exports = {
    doFilter,
    doInitFilter,
}
