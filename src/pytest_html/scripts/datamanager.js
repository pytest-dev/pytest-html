const { getCollapsedCategory } = require('./storage.js')

class DataManager {
    setManager(data) {
        const collapsedCategories = [...getCollapsedCategory(data.collapsed)]
        const dataBlob = { ...data, tests: Object.values(data.tests).flat().map((test, index) => ({
            ...test,
            id: `test_${index}`,
            collapsed: collapsedCategories.includes(test.result.toLowerCase()),
        })) }
        this.data = { ...dataBlob }
        this.renderData = { ...dataBlob }
    }

    get allData() {
        return { ...this.data }
    }
    resetRender() {
        this.renderData = { ...this.data }
    }
    setRender(data) {
        this.renderData.tests = [...data]
    }
    toggleCollapsedItem(id) {
        this.renderData.tests = this.renderData.tests.map((test) =>
            test.id === id ? { ...test, collapsed: !test.collapsed } : test,
        )
    }
    set allCollapsed(collapsed) {
        this.renderData = { ...this.renderData, tests: [...this.renderData.tests.map((test) => (
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
    get isFinished() {
        return this.data.runningState === 'Finished'
    }
}

module.exports = {
    manager: new DataManager(),
}
