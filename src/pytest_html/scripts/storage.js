const possibleFilters = [
    'passed',
    'skipped',
    'failed',
    'error',
    'xfailed',
    'xpassed',
    'rerun',
]

const getVisible = () => {
    const url = new URL(window.location.href)
    const settings = new URLSearchParams(url.search).get('visible')
    const lower = (item) => {
        const lowerItem = item.toLowerCase()
        if (possibleFilters.includes(lowerItem)) {
            return lowerItem
        }
        return null
    }
    return settings === null ?
        possibleFilters :
        [...new Set(settings?.split(',').map(lower).filter((item) => item))]
}

const hideCategory = (categoryToHide) => {
    const url = new URL(window.location.href)
    const visibleParams = new URLSearchParams(url.search).get('visible')
    const currentVisible = visibleParams ? visibleParams.split(',') : [...possibleFilters]
    const settings = [...new Set(currentVisible)].filter((f) => f !== categoryToHide).join(',')

    url.searchParams.set('visible', settings)
    window.history.pushState({}, null, unescape(url.href))
}

const showCategory = (categoryToShow) => {
    if (typeof window === 'undefined') {
        return
    }
    const url = new URL(window.location.href)
    const currentVisible = new URLSearchParams(url.search).get('visible')?.split(',').filter(Boolean) ||
        [...possibleFilters]
    const settings = [...new Set([categoryToShow, ...currentVisible])]
    const noFilter = possibleFilters.length === settings.length || !settings.length

    noFilter ? url.searchParams.delete('visible') : url.searchParams.set('visible', settings.join(','))
    window.history.pushState({}, null, unescape(url.href))
}

const getSort = (initialSort) => {
    const url = new URL(window.location.href)
    let sort = new URLSearchParams(url.search).get('sort')
    if (!sort) {
        sort = initialSort || 'result'
    }
    return sort
}

const setSort = (type) => {
    const url = new URL(window.location.href)
    url.searchParams.set('sort', type)
    window.history.pushState({}, null, unescape(url.href))
}

const getCollapsedCategory = (renderCollapsed) => {
    let categories
    if (typeof window !== 'undefined') {
        const url = new URL(window.location.href)
        const collapsedItems = new URLSearchParams(url.search).get('collapsed')
        switch (true) {
        case !renderCollapsed && collapsedItems === null:
            categories = ['passed']
            break
        case collapsedItems?.length === 0 || /^["']{2}$/.test(collapsedItems):
            categories = []
            break
        case /^all$/.test(collapsedItems) || collapsedItems === null && /^all$/.test(renderCollapsed):
            categories = [...possibleFilters]
            break
        default:
            categories = collapsedItems?.split(',').map((item) => item.toLowerCase()) || renderCollapsed
            break
        }
    } else {
        categories = []
    }
    return categories
}

const getSortDirection = () => JSON.parse(sessionStorage.getItem('sortAsc')) || false
const setSortDirection = (ascending) => sessionStorage.setItem('sortAsc', ascending)

const getCollapsedIds = () => JSON.parse(sessionStorage.getItem('collapsedIds')) || []
const setCollapsedIds = (list) => sessionStorage.setItem('collapsedIds', JSON.stringify(list))

module.exports = {
    getVisible,
    hideCategory,
    showCategory,
    getCollapsedIds,
    setCollapsedIds,
    getSort,
    setSort,
    getSortDirection,
    setSortDirection,
    getCollapsedCategory,
    possibleFilters,
}
