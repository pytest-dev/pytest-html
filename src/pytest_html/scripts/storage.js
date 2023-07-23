const possibleResults = [
    { result: 'passed', label: 'Passed' },
    { result: 'skipped', label: 'Skipped' },
    { result: 'failed', label: 'Failed' },
    { result: 'error', label: 'Errors' },
    { result: 'xfailed', label: 'Unexpected failures' },
    { result: 'xpassed', label: 'Unexpected passes' },
    { result: 'rerun', label: 'Reruns' },
]
const possibleFilters = possibleResults.map((item) => item.result)

const getVisible = () => {
    const url = new URL(window.location.href)
    const settings = new URLSearchParams(url.search).get('visible') || ''
    return settings ?
        [...new Set(settings.split(',').filter((filter) => possibleFilters.includes(filter)))] : possibleFilters
}
const hideCategory = (categoryToHide) => {
    const url = new URL(window.location.href)
    const visibleParams = new URLSearchParams(url.search).get('visible')
    const currentVisible = visibleParams ? visibleParams.split(',') : [...possibleFilters]
    const settings = [...new Set(currentVisible)].filter((f) => f !== categoryToHide).join(',')

    url.searchParams.set('visible', settings)
    history.pushState({}, null, unescape(url.href))
}

const showCategory = (categoryToShow) => {
    if (typeof window === 'undefined') {
        return
    }
    const url = new URL(window.location.href)
    const currentVisible = new URLSearchParams(url.search).get('visible')?.split(',') || [...possibleFilters]
    const settings = [...new Set([categoryToShow, ...currentVisible])]
    const noFilter = possibleFilters.length === settings.length || !settings.length

    noFilter ? url.searchParams.delete('visible') : url.searchParams.set('visible', settings.join(','))
    history.pushState({}, null, unescape(url.href))
}
const setFilter = (currentFilter) => {
    if (!possibleFilters.includes(currentFilter)) {
        return
    }
    const url = new URL(window.location.href)
    const settings = [currentFilter, ...new Set(new URLSearchParams(url.search).get('filter').split(','))]

    url.searchParams.set('filter', settings)
    history.pushState({}, null, unescape(url.href))
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
    history.pushState({}, null, unescape(url.href))
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

const getSortDirection = () => JSON.parse(sessionStorage.getItem('sortAsc'))

const setSortDirection = (ascending) => sessionStorage.setItem('sortAsc', ascending)

module.exports = {
    getVisible,
    setFilter,
    hideCategory,
    showCategory,
    getSort,
    getSortDirection,
    setSort,
    setSortDirection,
    getCollapsedCategory,
    possibleFilters,
    possibleResults,
}
