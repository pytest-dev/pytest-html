const possibleFilters = ['passed', 'skipped', 'failed', 'error', 'xfailed', 'xpassed', 'rerun']

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

const getSort = () => {
    const url = new URL(window.location.href)
    return new URLSearchParams(url.search).get('sort') || 'result'
}
const setSort = (type) => {
    const url = new URL(window.location.href)
    url.searchParams.set('sort', type)
    history.pushState({}, null, unescape(url.href))
}

const getCollapsedCategory = () => {
    let categotries
    if (typeof window !== 'undefined') {
        const url = new URL(window.location.href)
        const collapsedItems = new URLSearchParams(url.search).get('collapsed')
        categotries = collapsedItems?.split(',') || []
    } else {
        categotries = []
    }
    return categotries
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
}
