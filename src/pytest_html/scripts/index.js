const { redraw } = require('./main.js')
const { doInitFilter } = require('./filter.js')
const { doInitSort } = require('./sort.js')

function init() {
    doInitFilter()
    doInitSort()
    redraw()   
}

init()
