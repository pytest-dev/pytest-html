const formattedNumber = (number) =>
    number.toLocaleString('en-US', {
        minimumIntegerDigits: 2,
        useGrouping: false,
    })

const formatDuration = ( totalSeconds ) => {
    if (totalSeconds < 1) {
        return {ms: `${Math.round(totalSeconds * 1000)} ms`}
    }

    const hours = Math.floor(totalSeconds / 3600)
    let remainingSeconds = totalSeconds % 3600
    const minutes = Math.floor(remainingSeconds / 60)
    remainingSeconds = remainingSeconds % 60
    const seconds = Math.round(remainingSeconds)

    return {
      seconds: `${Math.round(totalSeconds)} seconds`,
      formatted: `${formattedNumber(hours)}:${formattedNumber(minutes)}:${formattedNumber(seconds)}`,
    }
}

module.exports = { formatDuration }
