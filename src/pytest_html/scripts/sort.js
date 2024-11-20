const { manager } = require('./datamanager.js')
const storageModule = require('./storage.js')

const genericSort = (list, key, ascending, customOrder) => {
    let sorted
    if (customOrder) {
        sorted = list.sort((a, b) => {
            const aValue = a.result.toLowerCase()
            const bValue = b.result.toLowerCase()

            const aIndex = customOrder.findIndex((item) => item.toLowerCase() === aValue)
            const bIndex = customOrder.findIndex((item) => item.toLowerCase() === bValue)

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

const durationSort = (list, ascending) => {
    const parseDuration = (duration) => {
        if (duration.includes(':')) {
            // If it's in the format "HH:mm:ss"
            const [hours, minutes, seconds] = duration.split(':').map(Number)
            return (hours * 3600 + minutes * 60 + seconds) * 1000
        } else {
            // If it's in the format "nnn ms"
            return parseInt(duration)
        }
    }
    const sorted = list.sort((a, b) => parseDuration(a['duration']) - parseDuration(b['duration']))
    if (ascending) {
        sorted.reverse()
    }
    return sorted
}

const doInitSort = () => {
    const type = storageModule.getSort(manager.initialSort)
    const ascending = storageModule.getSortDirection()
    const list = manager.testSubset
    const initialOrder = ['Error', 'Failed', 'Rerun', 'XFailed', 'XPassed', 'Skipped', 'Passed']

    storageModule.setSort(type)
    storageModule.setSortDirection(ascending)

    if (type?.toLowerCase() === 'original') {
        manager.setRender(list)
    } else {
        let sortedList
        switch (type) {
        case 'duration':
            sortedList = durationSort(list, ascending)
            break
        case 'result':
            sortedList = genericSort(list, type, ascending, initialOrder)
            break
        default:
            sortedList = genericSort(list, type, ascending)
            break
        }
        manager.setRender(sortedList)
    }
}

const doSort = (type, skipDirection) => {
    const newSortType = storageModule.getSort(manager.initialSort) !== type
    const currentAsc = storageModule.getSortDirection()
    let ascending
    if (skipDirection) {
        ascending = currentAsc
    } else {
        ascending = newSortType ? false : !currentAsc
    }
    storageModule.setSort(type)
    storageModule.setSortDirection(ascending)

    const list = manager.testSubset
    const sortedList = type === 'duration' ? durationSort(list, ascending) : genericSort(list, type, ascending)
    manager.setRender(sortedList)
}

module.exports = {
    doInitSort,
    doSort,
}
