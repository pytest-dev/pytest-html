const { manager } = require('./datamanager.js')
const localStorageModule = require('./localstorage_utils.js')

const getFilteredSubSet = (filter) =>
  manager.getRawObject().tests.filter(({ outcome }) => !filter.includes(outcome))

const doInitFilter = () => {
  const currentFilter = localStorageModule.getFilter()
  const filteredSubset = getFilteredSubSet(currentFilter)
  manager.setRender(filteredSubset)
}

const doFilter = (type, apply) => {
  const currentFilter = localStorageModule.getFilter()
  if (!apply) {
    currentFilter.push(type)
  } else {
    const index = currentFilter.indexOf(type);
    if (index > -1) {
      currentFilter.splice(index, 1)
    }
  }

  localStorageModule.setFilter(currentFilter)

  if (currentFilter.length) {
    const filteredSubset = getFilteredSubSet(currentFilter)
    manager.setRender(filteredSubset)
  } else {
    manager.resetRender()
  }
}

module.exports= {
  doFilter,
  doInitFilter,
}