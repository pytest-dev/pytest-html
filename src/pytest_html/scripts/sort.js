const { manager } = require('./datamanager.js')
const localStorageModule = require('./localstorage_utils.js')

const genericSort = (list, key, ascending) => {
    const sorted = list.sort((a, b) => a[key] === b[key] ? 0 : a[key] > b[key] ? 1 : -1)

    if (ascending) {
        sorted.reverse()
    }
    return sorted
}

const doInitSort = () => {
    const type = localStorageModule.getSort()
    const ascending = localStorageModule.getSortDirection()
    const list = manager.getRender()
    const sortedList = genericSort(list, type, ascending)
    manager.setRender(sortedList)
}

const doSort = (type) => {
    const newSortType = localStorageModule.getSort() !== type
    const currentAsc = localStorageModule.getSortDirection()
    const ascending = newSortType ? true : !currentAsc
    localStorageModule.setSort(type)
    localStorageModule.setSortDirection(ascending)
    const list = manager.getRender()

    const sortedList = genericSort(list, type, ascending)
    manager.setRender(sortedList)
}

exports.doSort = doSort
exports.doInitSort = doInitSort
