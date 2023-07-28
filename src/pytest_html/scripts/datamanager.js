const { getCollapsedCategory, setCollapsedIds } = require('./storage.js')

class DataManager {
    setManager(data) {
        const collapsedCategories = [...getCollapsedCategory(data.renderCollapsed)]
        const collapsedIds = []
        const tests = Object.values(data.tests).flat().map((test, index) => {
            const collapsed = collapsedCategories.includes(test.result.toLowerCase())
            const id = `test_${index}`
            if (collapsed) {
                collapsedIds.push(id)
            }
            return {
                ...test,
                id,
                collapsed,
            }
        })
        const dataBlob = { ...data, tests }
        this.data = { ...dataBlob }
        this.renderData = { ...dataBlob }
        setCollapsedIds(collapsedIds)
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

    get environment() {
        return this.renderData.environment
    }

    get initialSort() {
        return this.data.initialSort
    }
}

module.exports = {
    manager: new DataManager(),
}
