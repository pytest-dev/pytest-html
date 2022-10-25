const possibleFiltes = ['passed', 'skipped', 'failed', 'error', 'xfailed', 'xpassed', 'rerun']

const getVisible = () => {
    const url = new URL(window.location.href)
    const settings = new URLSearchParams(url.search).get('visible') || ''
    const toret = settings ?
        [...new Set(settings.split(',').filter((filter) => possibleFiltes.includes(filter)))] : possibleFiltes

    return toret
}
const hideCategory = (categoryToHide) => {
    const url = new URL(window.location.href)
    const visibleParams = new URLSearchParams(url.search).get('visible')
    const currentVisible = visibleParams ? visibleParams.split(',') : [...possibleFiltes]
    const settings = [...new Set(currentVisible)].filter((f) => f !== categoryToHide).join(',')

    url.searchParams.set('visible', settings)
    history.pushState({}, null, unescape(url.href))
}

const showCategory = (categoryToShow) => {
    const url = new URL(window.location.href)
    const currentVisible = new URLSearchParams(url.search).get('visible')?.split(',') || [...possibleFiltes]
    const settings = [...new Set([categoryToShow, ...currentVisible])]
    const noFilter = possibleFiltes.length === settings.length || !settings.length

    noFilter ? url.searchParams.delete('visible') : url.searchParams.set('visible', settings.join(','))
    history.pushState({}, null, unescape(url.href))
}
const setFilter = (currentFilter) => {
    if (!possibleFiltes.includes(currentFilter)) {
        return
    }
    const url = new URL(window.location.href)
    const settings = [currentFilter, ...new Set(new URLSearchParams(url.search).get('filter').split(','))]

    url.searchParams.set('filter', settings)
    history.pushState({}, null, unescape(url.href))
}

const getSort = () => {
    const url = new URL(window.location.href)
    return new URLSearchParams(url.search).get('sort') || 'outcome'
}
const setSort = (type) => {
    const url = new URL(window.location.href)
    url.searchParams.set('sort', type)
    history.pushState({}, null, unescape(url.href))
}

const getCollapsedCategory = () => {
    const url = new URL(window.location.href)
    const collapsedItems = new URLSearchParams(url.search).get('collapsed')
    return collapsedItems?.split(',') || []
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
