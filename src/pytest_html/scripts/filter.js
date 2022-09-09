const { manager } = require('./datamanager.js')
const storageModule = require('./storage.js')

const getFilteredSubSet = (filter) =>
    manager.allData.tests.filter(({ outcome }) => !filter.includes(outcome.toLowerCase()))

const doInitFilter = () => {
    const currentFilter = storageModule.getFilter()
    const filteredSubset = getFilteredSubSet(currentFilter)
    manager.setRender(filteredSubset)
}

const doFilter = (type, apply) => {
    const currentFilter = storageModule.getFilter()
    if (!apply) {
        currentFilter.push(type)
    } else {
        const index = currentFilter.indexOf(type)
        if (index > -1) {
            currentFilter.splice(index, 1)
        }
    }

    storageModule.setFilter(currentFilter)
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
