
const getFilter = () => ([
    ...new Set(JSON.parse(localStorage.getItem('filter')))
])
const setFilter = (currentFilter) => {
    localStorage.setItem('filter', JSON.stringify(currentFilter));
}

const getSort = () => {
    return localStorage.getItem('sort')
}
const setSort = (type) => {
    localStorage.setItem('sort', type)
}
const getSortDirection = () => {
    return JSON.parse(localStorage.getItem('sortAsc'))
}
const setSortDirection = (ascending) => {
    localStorage.setItem('sortAsc', ascending)
}

module.exports = { 
    getFilter, 
    setFilter,
    getSort,
    getSortDirection,
    setSort,
    setSortDirection
}