const { redraw, bindEvents, renderStatic } = require('./main.js')
const { doInitFilter } = require('./filter.js')
const { doInitSort } = require('./sort.js')
const { manager } = require('./datamanager.js')
const data = JSON.parse(document.getElementById('data-container').dataset.jsonblob)

function init() {
    manager.setManager(data)
    doInitFilter()
    doInitSort()
    renderStatic()
    redraw()
    bindEvents()
}

init()
