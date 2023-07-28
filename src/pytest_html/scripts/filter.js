const { manager } = require('./datamanager.js')
const { doSort } = require('./sort.js')
const storageModule = require('./storage.js')

const getFilteredSubSet = (filter) =>
    manager.allData.tests.filter(({ result }) => filter.includes(result.toLowerCase()))

const doInitFilter = () => {
    const currentFilter = storageModule.getVisible()
    const filteredSubset = getFilteredSubSet(currentFilter)
    manager.setRender(filteredSubset)
}

const doFilter = (type, show) => {
    if (show) {
        storageModule.showCategory(type)
    } else {
        storageModule.hideCategory(type)
    }

    const currentFilter = storageModule.getVisible()
    const filteredSubset = getFilteredSubSet(currentFilter)
    manager.setRender(filteredSubset)

    const sortColumn = storageModule.getSort()
    doSort(sortColumn, true)
}

module.exports = {
    doFilter,
    doInitFilter,
}
