/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/. */


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



function init() {
  // eslint-disable-line no-unused-vars
  setTimeout(() => {
    findAll('input[name="filter_checkbox"]').forEach((elem) => {
      elem.addEventListener('click', (evt) => {
        const { target: element } = evt;
        const { testResult } = element.dataset;

        doFilter(testResult, element.checked);
      });
    });
    initRender();
  });
}
