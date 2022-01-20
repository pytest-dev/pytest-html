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
  return toArray(elem.querySelectorAll(selector));
};
const templateEnvRow = find('#template_environment_row');
const templateResult = find('#template_results-table__tbody');
const aTag = find('#template_a');
const aTagImg = find('#template_img');
const listHeader = find('#template_results-table__head');
const listHeaderEmpty = find('#template_results-table__head--empty');

const removeChildren = (node) => {
  while (node.firstChild) {
    node.removeChild(node.firstChild);
  }
};

const getOutcome = ({ nodeid }, tests) => {
  const relatedOutcome = tests
    .filter((test) => test.nodeid === nodeid)
    .map(({ outcome }) => outcome);
  if (relatedOutcome.includes('failed')) {
    return 'failed';
  } else if (relatedOutcome.includes('error')) {
    return 'error';
  } else if (relatedOutcome.includes('xpassed')) {
    return 'xpassed';
  } else if (relatedOutcome.includes('xfailed')) {
    return 'xfailed';
  } else if (relatedOutcome.includes('skipped')) {
    return 'skipped';
  } else {
    return 'passed';
  }
};

const renderStatic = (obj) => {
  find('#title').innerText = obj.title;
  find('#head-title').innerText =obj.title;
  const rows = Object.keys(obj.environment).map((key) =>
    dom.getStaticRow(key, obj.environment[key])
  );

  const table = find('#environment');
  removeChildren(table);
  rows.forEach((row) => table.appendChild(row));
};
const renderContent = ({ tests }) => {
  const renderSet = tests.filter(({ when }) => when === 'call');

  const rows = renderSet.map((test) =>
    dom.getResultTBody(test, getOutcome(test, tests))
  );
  const table = find('#results-table');
  removeChildren(table);
  const tableHeader = dom.getListHeader();
  if (!rows.length) {
    tableHeader.appendChild(dom.getListHeaderEmpty());
  }
  table.appendChild(tableHeader);

  rows.forEach((row) => !!row && table.appendChild(row));
};
const renderDerrived = ({ tests, collectedItems }) => {
  const renderSet = tests.filter(({ when }) => when === 'call');

  const possibleOutcomes = [
    'passed',
    'skipped',
    'failed',
    'error',
    'xfailed',
    'xpassed',
    'rerun',
  ];
  possibleOutcomes.forEach((outcome) => {
    const count = renderSet.filter((test) => test.outcome === outcome).length;

    find(`.${outcome}`).innerText = `${count} ${outcome}`;
    if (!count) {
      find(`input[data-test-result="${outcome}"]`).disabled = true;
    }
  });

  let accTime = 0;
  if (collectedItems === renderSet.length) {
    tests.forEach(({ duration }) => (accTime += duration));
    accTime = accTime.toFixed(2);
    find(
      '.run-count'
    ).innerText = `${renderSet.length} tests ran in ${accTime} seconds.`;
    find('.summary__reload__button').classList.add('hidden');
  } else {
    find(
      '.run-count'
    ).innerText = `${renderSet.length} / ${collectedItems} tests done`;
  }
};

const bindEvents = () => {
  findAll('.sortable').forEach((elem) => {
    elem.addEventListener('click', (evt) => {
      const { target: element } = evt;
      const { columnType } = element.dataset;

      doSort(columnType);
    });
  });
};

const renderPage = (subset, full) => {
  renderStatic(jsonData);
  renderContent(renderData);
  renderDerrived(jsonData);
};
let renderData = { ...jsonData };
const initRender = () => {
  setTimeout(() => {
    renderPage(renderData);
    bindEvents();
  }, 0);
};
