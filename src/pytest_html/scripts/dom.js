const storageModule = require('./storage.js')
const { formatDuration } = require('./utils.js')
const mediaViewer = require('./mediaviewer.js')
const templateEnvRow = document.querySelector('#template_environment_row')
const templateCollGroup = document.querySelector('#template_table-colgroup')
const templateResult = document.querySelector('#template_results-table__tbody')
const aTag = document.querySelector('#template_a')
const listHeader = document.querySelector('#template_results-table__head')
const listHeaderEmpty = document.querySelector('#template_results-table__head--empty')

function htmlToElements(html) {
    const temp = document.createElement('template')
    temp.innerHTML = html
    return temp.content.childNodes
}

const find = (selector, elem) => {
    if (!elem) {
        elem = document
    }
    return elem.querySelector(selector)
}

const findAll = (selector, elem) => {
    if (!elem) {
        elem = document
    }
    return [...elem.querySelectorAll(selector)]
}

const insertAdditionalHTML = (html, element, selector) => {
    Object.keys(html).map((key) => {
        element.querySelectorAll(selector).item(key).insertAdjacentHTML('beforebegin', html[key])
    })
}

const dom = {
    getStaticRow: (key, value) => {
        const envRow = templateEnvRow.content.cloneNode(true)
        const isObj = typeof value === 'object' && value !== null
        const values = isObj ? Object.keys(value).map((k) => `${k}: ${value[k]}`) : null

        const valuesElement = htmlToElements(
            values ? `<ul>${values.map((val) => `<li>${val}</li>`).join('')}<ul>` : `<div>${value}</div>`)[0]
        const td = findAll('td', envRow)
        td[0].textContent = key
        td[1].appendChild(valuesElement)

        return envRow
    },
    getListHeader: ({ resultsTableHeader }) => {
        const header = listHeader.content.cloneNode(true)
        const sortAttr = storageModule.getSort()
        const sortAsc = JSON.parse(storageModule.getSortDirection())

        const regex = /data-column-type="(\w+)/
        const cols = Object.values(resultsTableHeader).reduce((result, value) => {
            if (value.includes("sortable")) {
                const matches = regex.exec(value)
                if (matches) {
                    result.push(matches[1])
                }
            }
            return result
        }, [])
        const sortables = ['result', 'testId', 'duration', ...cols]

        // Add custom html from the pytest_html_results_table_header hook
        insertAdditionalHTML(resultsTableHeader, header, 'th')

        sortables.forEach((sortCol) => {
            if (sortCol === sortAttr) {
                header.querySelector(`[data-column-type="${sortCol}"]`).classList.add(sortAsc ? 'desc' : 'asc')
            }
        })

        return header
    },
    getListHeaderEmpty: () => listHeaderEmpty.content.cloneNode(true),
    getColGroup: () => templateCollGroup.content.cloneNode(true),
    getResultTBody: ({ testId, id, log, duration, extras, resultsTableRow, tableHtml, result, collapsed }) => {
        const resultLower = result.toLowerCase()
        let formattedDuration = formatDuration(duration)
        formattedDuration = formatDuration < 1 ? formattedDuration.ms : formattedDuration.formatted
        const resultBody = templateResult.content.cloneNode(true)
        resultBody.querySelector('tbody').classList.add(resultLower)
        resultBody.querySelector('tbody').id = testId
        resultBody.querySelector('.col-result').innerText = result
        resultBody.querySelector('.col-result').classList.add(`${collapsed ? 'expander' : 'collapser'}`)
        resultBody.querySelector('.col-result').dataset.id = id
        resultBody.querySelector('.col-name').innerText = testId

        resultBody.querySelector('.col-duration').innerText = duration < 1 ? formatDuration(duration).ms : formatDuration(duration).formatted


        if (log) {
            resultBody.querySelector('.log').innerHTML = log
        } else {
            resultBody.querySelector('.log').remove()
        }

        if (collapsed) {
            resultBody.querySelector('.extras-row').classList.add('hidden')
        }

        const media = []
        extras?.forEach(({ name, format_type, content }) => {
            if (['json', 'text', 'url'].includes(format_type)) {
                const extraLink = aTag.content.cloneNode(true)
                const extraLinkItem = extraLink.querySelector('a')

                extraLinkItem.href = content
                extraLinkItem.className = `col-links__extra ${format_type}`
                extraLinkItem.innerText = name
                resultBody.querySelector('.col-links').appendChild(extraLinkItem)
            }

            if (['image', 'video'].includes(format_type)) {
                media.push({ path: content, name, format_type })
            }

            if (format_type === 'html') {
                resultBody.querySelector('.extraHTML').insertAdjacentHTML('beforeend', `<div>${content}</div>`)
            }
        })
        mediaViewer.setUp(resultBody, media)

        // Add custom html from the pytest_html_results_table_row hook
        resultsTableRow && insertAdditionalHTML(resultsTableRow, resultBody, 'td')

        // Add custom html from the pytest_html_results_table_html hook
        tableHtml?.forEach((item) => {
            resultBody.querySelector('td[class="extra"]').insertAdjacentHTML('beforeend', item)
        })

        return resultBody
    },
}

exports.dom = dom
exports.htmlToElements = htmlToElements
exports.find = find
exports.findAll = findAll
