const mediaViewer = require('./mediaviewer.js')
const templateEnvRow = document.getElementById('template_environment_row')
const templateResult = document.getElementById('template_results-table__tbody')
const listHeaderEmpty = document.getElementById('template_results-table__head--empty')

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
    getListHeaderEmpty: () => listHeaderEmpty.content.cloneNode(true),
    getResultTBody: ({ testId, id, log, duration, extras, resultsTableRow, tableHtml, result, collapsed }) => {
        const resultLower = result.toLowerCase()
        const resultBody = templateResult.content.cloneNode(true)
        resultBody.querySelector('tbody').classList.add(resultLower)
        resultBody.querySelector('tbody').id = testId
        resultBody.querySelector('.collapsible').dataset.id = id

        resultsTableRow.forEach((html) => {
            const t = document.createElement('template')
            t.innerHTML = html
            resultBody.querySelector('.collapsible').appendChild(t.content)
        })

        if (log) {
            // Wrap lines starting with "E" with span.error to color those lines red
            const wrappedLog = log.replace(/^E.*$/gm, (match) => `<span class="error">${match}</span>`)
            resultBody.querySelector('.log').innerHTML = wrappedLog
        } else {
            resultBody.querySelector('.log').remove()
        }

        if (collapsed) {
            resultBody.querySelector('.collapsible > td')?.classList.add('collapsed')
            resultBody.querySelector('.extras-row').classList.add('hidden')
        } else {
            resultBody.querySelector('.collapsible > td')?.classList.remove('collapsed')
        }

        const media = []
        extras?.forEach(({ name, format_type, content }) => {
            if (['image', 'video'].includes(format_type)) {
                media.push({ path: content, name, format_type })
            }

            if (format_type === 'html') {
                resultBody.querySelector('.extraHTML').insertAdjacentHTML('beforeend', `<div>${content}</div>`)
            }
        })
        mediaViewer.setup(resultBody, media)

        // Add custom html from the pytest_html_results_table_html hook
        tableHtml?.forEach((item) => {
            resultBody.querySelector('td[class="extra"]').insertAdjacentHTML('beforeend', item)
        })

        return resultBody
    },
}

module.exports = {
    dom,
    htmlToElements,
    find,
    findAll,
}
