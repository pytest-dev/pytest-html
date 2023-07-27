const { getCollapsedCategory } = require('./storage.js')

class DataManager {
    setManager(data) {
        const collapsedCategories = [...getCollapsedCategory(data.renderCollapsed)]
        const tests = Object.values(data.tests).flat().map((test, index) => {
            const collapsed = collapsedCategories.includes(test.result.toLowerCase())
            return {
                ...test,
                id: `test_${index}`,
                collapsed,
            }
        })
        const dataBlob = { ...data, tests }
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
        console.log("render data before:")
        console.log(this.renderData)
        this.renderData = { ...this.renderData, tests: [...this.renderData.tests.map((test) => (
            { ...test, collapsed }
        ))] }
        console.log("render data after:")
        console.log(this.renderData)
    }

    get testSubset() {
        return [...this.renderData.tests]
    }

    get environment() {
        return this.renderData.environment
    }
}

module.exports = {
    manager: new DataManager(),
}
