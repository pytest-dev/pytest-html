class DataManager {
    setManager(data) {
        this.data = { ...data }
        this.renderData = { ...data }
    }
    getRawObject() {
        return { ...this.data }
    }
    resetRender() {
        this.renderData = { ...this.data }
    }
    setRender(data) {
        this.renderData.tests = data
    }
    getRender() {
        return [...this.renderData.tests]
    }
    getRaw() {
        return [...this.data.tests]
    }
    getTitle() {
        return this.renderData.title
    }
    getEnvironment() {
        return this.renderData.environment
    }
    getCollectedItems() {
        return this.renderData.collectedItems
    }
    getDurationFormat() {
        return this.renderData.durationFormat
    }
}

module.exports = {
    manager: new DataManager(),
}
