const { manager } = require('./datamanager.js')
const storageModule = require('./storage.js')

const genericSort = (list, key, ascending) => {
    const sorted = list.sort((a, b) => a[key] === b[key] ? 0 : a[key] > b[key] ? 1 : -1)

    if (ascending) {
        sorted.reverse()
    }
    return sorted
}

const doInitSort = () => {
    const type = storageModule.getSort()
    const ascending = storageModule.getSortDirection()
    const list = manager.testSubset
    const sortedList = genericSort(list, type, ascending)
    manager.setRender(sortedList)
}

const doSort = (type) => {
    const newSortType = storageModule.getSort() !== type
    const currentAsc = storageModule.getSortDirection()
    const ascending = newSortType ? true : !currentAsc
    storageModule.setSort(type)
    storageModule.setSortDirection(ascending)
    const list = manager.testSubset

    const sortedList = genericSort(list, type, ascending)
    manager.setRender(sortedList)
}

exports.doSort = doSort
exports.doInitSort = doInitSort
