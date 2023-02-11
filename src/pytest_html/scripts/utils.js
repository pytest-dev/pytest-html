const formatedNumber = (number) =>
    number.toLocaleString('en-US', {
        minimumIntegerDigits: 2,
        useGrouping: false,
    })


const formatDuration = ( ms ) => {
    const totalSeconds = ms / 1000

    if (totalSeconds < 1) {
        return `${ms}ms`
    }
    const hours = Math.floor(totalSeconds / 3600)
    let remainingSeconds = totalSeconds % 3600
    const minutes = Math.floor(remainingSeconds / 60)
    remainingSeconds = remainingSeconds % 60
    const seconds = Math.round(remainingSeconds)

    return `${formatedNumber(hours)}:${formatedNumber(minutes)}:${formatedNumber(seconds)}`
}

module.exports = { formatDuration }
