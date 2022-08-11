class DataManager {
    setManager(data) {
        this.data = { ...data }
        this.renderData = { ...data }
    }
    get allData() {
        return { ...this.data }
    }
    resetRender() {
        this.renderData = { ...this.data }
    }
    setRender(data) {
        this.renderData.tests = data
    }

    set allCollapsed(collapsed) {
        this.renderData = { ...this.data, tests: [...this.data.tests.map((test) => (
            { ...test, collapsed }
        ))] }
    }

    get testSubset() {
        return [...this.renderData.tests]
    }
    get allTests() {
        return [...this.data.tests]
    }
    get title() {
        return this.renderData.title
    }
    get environment() {
        return this.renderData.environment
    }
    get collectedItems() {
        return this.renderData.collectedItems
    }
    get durationFormat() {
        return this.renderData.durationFormat
    }
    get isFinished() {
        return this.data.runningState === 'Finished'
    }
}

module.exports = {
    manager: new DataManager(),
}
