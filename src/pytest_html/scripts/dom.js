const templateEnvRow = document.querySelector('#template_environment_row');
const templateResult = document.querySelector('#template_results-table__tbody');
const aTag = document.querySelector('#template_a');
const aTagImg = document.querySelector('#template_img');
const listHeader = document.querySelector('#template_results-table__head');
const listHeaderEmpty = document.querySelector('#template_results-table__head--empty');

function htmlToElements(html) {
  let temp = document.createElement('template');
  temp.innerHTML = html;
  return temp.content.childNodes;
}

const find = (selector, elem) => {
  if (!elem) {
    elem = document;
  }
  return elem.querySelector(selector);
};

const findAll = (selector, elem) => {
  if (!elem) {
    elem = document;
  }
  return [...elem.querySelectorAll(selector)];
};

const dom = {
  getStaticRow: (key, value) => {
    const envRow = templateEnvRow.content.cloneNode(true);
    const isObj = typeof value === 'object' && value !== null;
    const values = isObj
      ? Object.keys(value).map((k) => `${k}: ${value[k]}`)
      : null;

    const valuesElement = htmlToElements(
      values
        ? `<ul>${values.map((val) => `<li>${val}</li>`).join('')}<ul>`
        : `<div>${value}</div>`
    )[0];
    var td = findAll('td', envRow);
    td[0].textContent = key;
    td[1].appendChild(valuesElement);

    return envRow;
  },
  getListHeader: () => {
    const header = listHeader.content.cloneNode(true);
    const sortAttr = localStorage.getItem('sort');
    const sortAsc = JSON.parse(localStorage.getItem('sortAsc'));
    const sortables = ['outcome', 'nodeid', 'duration'];

    sortables.forEach((sortCol) => {
      if (sortCol === sortAttr) {
        header.querySelector(`[data-column-type="${sortCol}"]`).classList.add(
          sortAsc ? 'desc' : 'asc'
        );
      }
    });

    return header;
  },
  getListHeaderEmpty: () => listHeaderEmpty.content.cloneNode(true),
  getResultTBody: ({ nodeid, longrepr, extras, duration }, outcome) => {
    const resultBody = templateResult.content.cloneNode(true);
    resultBody.querySelector('tbody').classList.add(outcome);
    resultBody.querySelector('.col-result').innerText = outcome;
    resultBody.querySelector('.col-name').innerText = nodeid;
    resultBody.querySelector('.col-duration').innerText = `${(duration * 1000).toFixed(2)}s`;
    if (outcome === 'failed') {
      resultBody.querySelector('.log').innerText = longrepr
        ? longrepr.reprtraceback.reprentries[0].data.lines.join('\n')
        : '';
    } else {
      resultBody.querySelector('.extras-row').classList.add('hidden');
    }

    extras &&
      extras.forEach(({ name, format_type, content }) => {
        const extraLink = aTag.content.cloneNode(true);
        const extraLinkItem = extraLink.querySelector('a');
        const folderItems = ['image', 'video', 'text', 'html', 'json'];

        extraLinkItem.href = content;
        extraLinkItem.className = `col-links__extra ${format_type}`;
        extraLinkItem.innerText = name;
        resultBody.querySelector('.col-links').appendChild(extraLinkItem);

        if (format_type === 'image') {
          const imgElTemp = aTagImg.content.cloneNode(true);
          imgElTemp.querySelector('a').href = content;
          imgElTemp.querySelector('img').src = content;
          resultBody.querySelector('.extra .image').appendChild(imgElTemp);
        }
      });

    return resultBody;
  },
};

exports.dom = dom
exports.htmlToElements = htmlToElements
exports.find = find
exports.findAll = findAll
