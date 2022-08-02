const { redraw } = require('./main.js')
const { doInitFilter } = require('./filter.js')
const { doInitSort } = require('./sort.js')
const { manager } = require('./datamanager.js')
const data = JSON.parse(document.querySelector('#data-container').dataset.jsonblob)

function init() {
    manager.setManager(data)
    doInitFilter()
    doInitSort()
    redraw()
}

init()
