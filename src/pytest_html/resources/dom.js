// const templateEnvRow = find('#template_environment_row');
// const templateResult = find('#template_results-table__tbody');
// const aTag = find('#template_a');
// const aTagImg = find('#template_img');
// const listHeader = find('#template_results-table__head');
const dom = {
  getStaticRow: (key, value) => {
    var envRow = templateEnvRow.content.cloneNode(true);
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
        find(`[data-column-type="${sortCol}"]`, header).classList.add(
          sortAsc ? 'desc' : 'asc'
        );
      }
    });

    return header;
  },
  getListHeaderEmpty: () => listHeaderEmpty.content.cloneNode(true),
  getResultTBody: ({ nodeid, longrepr, extras, duration }, outcome) => {
    const isFail = outcome === 'failed';
    const resultBody = templateResult.content.cloneNode(true);
    find('tbody', resultBody).classList.add(outcome);

    find('.col-result', resultBody).innerText = outcome;
    find('.col-name', resultBody).innerText = nodeid;
    find('.col-duration', resultBody).innerText = `${(duration * 1000).toFixed(
      2
    )}s`;
    if (isFail) {
      find('.log', resultBody).innerText = longrepr
        ? longrepr.reprtraceback.reprentries[0].data.lines.join('\n')
        : '';
    } else {
      find('.extras-row', resultBody).classList.add('hidden');
    }

    extras &&
      extras.forEach(({ name, format_type, content }) => {
        const extraLink = aTag.content.cloneNode(true);
        const extraLinkItem = find('a', extraLink);
        const folderItems = ['image', 'video', 'text', 'html', 'json'];

        extraLinkItem.href = `${
          folderItems.includes(format_type) ? 'assets/' : ''
        }${content}`;
        extraLinkItem.className = `col-links__extra ${format_type}`;
        extraLinkItem.innerText = name;
        find('.col-links', resultBody).appendChild(extraLinkItem);
        if (format_type === 'image') {
          const imgElTemp = aTagImg.content.cloneNode(true);
          find('a', imgElTemp).href = `assets/${content}`;
          find('img', imgElTemp).src = `assets/${content}`;
          find('.extra .image', resultBody).appendChild(imgElTemp);
        }
      });

    return resultBody;
  },
};
