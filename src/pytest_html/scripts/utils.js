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

const transformTableObj = (obj) => {
    const appends = {}
    const inserts = {}
    for (const key in obj) {
        key.startsWith("Z") ? appends[key] = obj[key] : inserts[key] = obj[key]
    }
    return {
        appends,
        inserts,
    }
}

module.exports = {
    formatDuration,
    transformTableObj,
}
