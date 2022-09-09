const getFilter = () => [...new Set(JSON.parse(sessionStorage.getItem('filter')))]
const setFilter = (currentFilter) => {
    sessionStorage.setItem('filter', JSON.stringify(currentFilter))
}

const getSort = () => sessionStorage.getItem('sort')
const setSort = (type) => sessionStorage.setItem('sort', type)

const getSortDirection = () => JSON.parse(sessionStorage.getItem('sortAsc'))

const setSortDirection = (ascending) => {
    sessionStorage.setItem('sortAsc', ascending)
}

module.exports = {
    getFilter,
    setFilter,
    getSort,
    getSortDirection,
    setSort,
    setSortDirection,
}
