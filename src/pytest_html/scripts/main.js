const { dom, findAll } = require('./dom.js')
const { manager } = require('./datamanager.js')
const { doSort } = require('./sort.js')
const { doFilter } = require('./filter.js')
const { getFilter } = require('./localstorage_utils.js')

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

const renderStatic = () => {
  const title = manager.title
  const environment = manager.environment
  document.querySelector('#title').innerText = title;
  document.querySelector('#head-title').innerText = title;
  const rows = Object.keys(environment).map((key) =>
    dom.getStaticRow(key, environment[key])
  );

  const table = document.querySelector('#environment');
  removeChildren(table);
  rows.forEach((row) => table.appendChild(row));
};

const renderContent = (tests) => {
  const renderSet = tests.filter(({ when }) => when === 'call');

  const rows = renderSet.map((test) =>
    dom.getResultTBody(test, getOutcome(test, tests))
  );
  const table = document.querySelector('#results-table');
  removeChildren(table);
  const tableHeader = dom.getListHeader();
  if (!rows.length) {
    tableHeader.appendChild(dom.getListHeaderEmpty());
  }
  table.appendChild(tableHeader);

  rows.forEach((row) => !!row && table.appendChild(row));
};

const renderDerived = (tests, collectedItems) => {
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
  const currentFilter = getFilter()
  possibleOutcomes.forEach((outcome) => {
    const count = renderSet.filter((test) => test.outcome === outcome).length;
    const input = document.querySelector(`input[data-test-result="${outcome}"]`)
    document.querySelector(`.${outcome}`).innerText = `${count} ${outcome}`;

    input.disabled = !count;
    input.checked = !currentFilter.includes(outcome)
  });


  if (collectedItems === renderSet.length) {
    const accTime = tests.reduce((prev, { duration }) => prev + duration, 0).toFixed(2)

    document.querySelector('.run-count').innerText = `${renderSet.length} tests ran in ${accTime} seconds.`;
    document.querySelector('.summary__reload__button').classList.add('hidden');
  } else {
    document.querySelector('.run-count').innerText = `${renderSet.length} / ${collectedItems} tests done`;
  }
};

const bindEvents = () => {
  findAll('.sortable').forEach((elem) => {
    elem.addEventListener('click', (evt) => {
      const { target: element } = evt;
      const { columnType } = element.dataset;

      doSort(columnType);
      redraw();
    });
  });
  findAll('input[name="filter_checkbox"]').forEach((elem) => {
    elem.addEventListener('click', (evt) => {
      const { target: element } = evt
      const { testResult } = element.dataset

      doFilter(testResult, element.checked)
      redraw()
    });
  });
};

const renderPage = () => {
  const filteredTests = manager.testSubset
  const allTests = manager.allTests
  const collectedItems = manager.collectedItems

  renderStatic();
  renderContent(filteredTests);
  renderDerived(allTests, collectedItems);
};

const redraw = () => {
  setTimeout(() => {
    renderPage();
    bindEvents();
  }, 0);
};

function showAllExtras() {
  // eslint-disable-line no-unused-vars
  findAll('.col-result').forEach(showExtras);
}

function hideAllExtras() {
  // eslint-disable-line no-unused-vars
  findAll('.col-result').forEach(hideExtras);
}

function showExtras(colresultElem) {
  const extras = colresultElem.parentNode.nextElementSibling;
  const expandcollapse = colresultElem.firstElementChild;
  extras.classList.remove('collapsed');
  expandcollapse?.classList.remove('expander');
  expandcollapse?.classList.add('collapser');
}

function hideExtras(colresultElem) {
  const extras = colresultElem.parentNode.nextElementSibling;
  const expandcollapse = colresultElem.firstElementChild;
  extras.classList.add('collapsed');
  expandcollapse?.classList.remove('collapser');
  expandcollapse?.classList.add('expander');
}

exports.redraw = redraw
