const { manager } = require('./datamanager.js')
const storageModule = require('./storage.js')

const genericSort = (list, key, ascending, customOrder) => {
    let sorted
    if (customOrder) {
        sorted = list.sort((a, b) => {
            const aValue = a.result.toLowerCase()
            const bValue = b.result.toLowerCase()

            const aIndex = customOrder.findIndex(item => item.toLowerCase() === aValue)
            const bIndex = customOrder.findIndex(item => item.toLowerCase() === bValue)

            // Compare the indices to determine the sort order
            return aIndex - bIndex
        })
    } else {
        sorted = list.sort((a, b) => a[key] === b[key] ? 0 : a[key] > b[key] ? 1 : -1)
    }

    if (ascending) {
        sorted.reverse()
    }
    return sorted
}

const doInitSort = () => {
    const type = storageModule.getSort()
    const ascending = storageModule.getSortDirection()
    const list = manager.testSubset
    const initialOrder = ['Error', 'Failed', 'Rerun', 'XFailed', 'XPassed', 'Skipped', 'Passed']
    if (type?.toLowerCase() === 'original') {
        manager.setRender(list)
    } else {
        const sortedList = genericSort(list, type, ascending, initialOrder)
        manager.setRender(sortedList)
    }
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
