const { formatDuration } = require('./utils.js')
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

const getOutcome = ({ nodeid, wasxfail }, tests) => {
  const relatedOutcome = tests
    .filter((test) => test.nodeid === nodeid)
    .map(({ outcome }) => outcome);
  if (relatedOutcome.includes('failed')) {
    return (wasxfail === undefined) ? 'Failed' : 'XPassed';
  } else if (relatedOutcome.includes('error')) {
    return 'Error';
  } else if (relatedOutcome.includes('skipped')) {
    return (wasxfail === undefined) ? 'Skipped' : 'XFailed';
  } else {
    return (wasxfail === undefined) ? 'Passed' : 'XPassed';
  }
};

const renderStatic = () => {
  const title = manager.getTitle()
  const environment = manager.getEnvironment()
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
  const tableHeader = dom.getListHeader(manager.renderData);
  if (!rows.length) {
    tableHeader.appendChild(dom.getListHeaderEmpty());
  }

  table.appendChild(tableHeader);

  rows.forEach((row) => !!row && table.appendChild(row));

  table.querySelectorAll('.extra').forEach((item) => {
      item.colSpan = document.querySelectorAll('th').length;
  });
};

const renderDerived = (tests, collectedItems) => {
  const renderSet = tests.filter(({ when }) => when === 'call');

  const possibleOutcomes = [
    {outcome: 'passed', label: 'Passed'},
    {outcome: 'skipped', label: 'Skipped'},
    {outcome: 'failed', label: 'Failed'},
    {outcome: 'error', label: 'Errors'},
    {outcome: 'xfailed', label: 'Unexpected failures'},
    {outcome: 'xpassed', label: 'Unexpected passes'},
    {outcome: 'rerun', label: 'Reruns'},
  ];

  const currentFilter = getFilter()
  possibleOutcomes.forEach(({outcome, label}) => {
    const count = renderSet.filter((test) => {
      const wasXpassed = outcome === 'xpassed' && ['passed', 'failed'].includes(test.outcome);
      const wasXfailed = outcome === 'xfailed' && test.outcome === 'skipped';
      if (test.wasxfail !== undefined) {
        return wasXpassed || wasXfailed;
      } else {
        return test.outcome === outcome;
      }
    }).length;
    const input = document.querySelector(`input[data-test-result="${outcome}"]`)
    document.querySelector(`.${outcome}`).innerText = `${count} ${label}`;

    input.disabled = !count;
    input.checked = !currentFilter.includes(outcome)
  });

  if (collectedItems === renderSet.length) {
    const accTime = tests.reduce((prev, { duration }) => prev + duration, 0)
    const formattedAccTime = formatDuration(accTime)
    const testWord = renderSet.length > 1 ? 'tests' : 'test'
    const innerText = `${renderSet.length} ${testWord} ran in ${formattedAccTime} seconds.`
    document.querySelector('.run-count').innerText = innerText;
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
  const filteredTests = manager.getRender()
  const allTests = manager.getRaw()
  const collectedItems = manager.getCollectedItems()

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
  expandcollapse && expandcollapse.classList.remove('expander');
  expandcollapse && expandcollapse.classList.add('collapser');
}

function hideExtras(colresultElem) {
  const extras = colresultElem.parentNode.nextElementSibling;
  const expandcollapse = colresultElem.firstElementChild;
  extras.classList.add('collapsed');
  expandcollapse && expandcollapse.classList.remove('collapser');
  expandcollapse && expandcollapse.classList.add('expander');
}

exports.redraw = redraw
