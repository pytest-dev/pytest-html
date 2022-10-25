const { manager } = require('./datamanager.js')
const storageModule = require('./storage.js')

const getFilteredSubSet = (filter) =>
    manager.allData.tests.filter(({ outcome }) => filter.includes(outcome.toLowerCase()))

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

    if (currentFilter.length) {
        const filteredSubset = getFilteredSubSet(currentFilter)
        manager.setRender(filteredSubset)
    } else {
        manager.resetRender()
    }
}

module.exports= {
    doFilter,
    doInitFilter,
}
