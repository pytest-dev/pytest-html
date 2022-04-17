const { jsonData } = require('./test_data.js')

class DataManager {
    constructor(data){
        this.data = { ...data }
        this.renderData = { ...data }
    }
    getRawObject() {
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
}

module.exports = {
    manager: new DataManager(jsonData)
}