const { manager } = require('./datamanager.js')

const dayjs = require('dayjs')
const duration = require('dayjs/plugin/duration')
dayjs.extend(duration)

const formatDuration = (dur) => {
    const durationFormat = manager.durationFormat
    if (durationFormat.length === 0) {
        return dur.toFixed(2)
    } else {
        return dayjs.duration(dur * 1000).format(durationFormat)
    }
}

module.exports = { formatDuration }
