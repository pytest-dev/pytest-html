/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/. */


function toArray(iter) {
    if (iter === null) {
        return null;
    }
    return Array.prototype.slice.call(iter);
}

function find(selector, elem) { // eslint-disable-line no-redeclare
    if (!elem) {
        elem = document;
    }
    return elem.querySelector(selector);
}

function findAll(selector, elem) {
    if (!elem) {
        elem = document;
    }
    return toArray(elem.querySelectorAll(selector));
}

function sortColumn(elem) {
    toggleSortStates(elem);
    const table = elem.parentNode.parentNode.parentNode;
    const colIndex = toArray(elem.parentNode.childNodes).indexOf(elem);

    let key;
    if (elem.classList.contains('result')) {
        key = keyResult;
    } else if (elem.classList.contains('links')) {
        key = keyLink;
    } else {
        key = keyAlpha;
    }

    sortTable(table, elem, key(colIndex));
}

function showAllExtras() { // eslint-disable-line no-unused-vars
    findAll('.results-table-row').forEach(showExtras);
}

function hideAllExtras() { // eslint-disable-line no-unused-vars
    findAll('.results-table-row').forEach(hideExtras);
}

function showExtras(resultsTableRowElem) {
    const extras = resultsTableRowElem.lastElementChild;
    extras.classList.remove('collapsed');
}

function hideExtras(resultsTableRowElem) {
    const extras = resultsTableRowElem.lastElementChild;
    extras.classList.add('collapsed');
}

function showFilters() {
    let visibleString = getQueryParameter('visible') || 'all';
    visibleString = visibleString.toLowerCase();
    const checkedItems = visibleString.split(',');

    const filterItems = document.getElementsByClassName('filter');
    for (let i = 0; i < filterItems.length; i++) {
        filterItems[i].hidden = false;

        if (visibleString != 'all') {
            filterItems[i].checked = checkedItems.includes(filterItems[i].getAttribute('data-test-result'));
            filterTable(filterItems[i]);
        }
    }
}

function addCollapse() {
    // Add links for show/hide all
    findAll('.results-table').forEach(function(table) {
        const showhideall = document.createElement('p');
        showhideall.innerHTML = '<a href="javascript:showAllExtras()">Show all details</a> / ' +
                                '<a href="javascript:hideAllExtras()">Hide all details</a>';
        table.parentElement.insertBefore(showhideall, table);
    });

    // Add show/hide link to each result
    findAll('.results-table-row').forEach(function(elem) {
        const collapsed = getQueryParameter('collapsed') || 'Passed';
        const extras = elem.lastElementChild;

        if (elem.classList.contains(collapsed.toLowerCase())) {
            extras.classList.add('collapsed');
        }

        elem.firstElementChild.addEventListener('click', function(event) {
            if (event.currentTarget.parentNode.lastElementChild.classList.contains('collapsed')) {
                showExtras(event.currentTarget.parentNode);
            } else {
                hideExtras(event.currentTarget.parentNode);
            }
        });
    });

}

function getQueryParameter(name) {
    const match = RegExp('[?&]' + name + '=([^&]*)').exec(window.location.search);
    return match && decodeURIComponent(match[1].replace(/\+/g, ' '));
}

function init () { // eslint-disable-line no-unused-vars
    resetSortHeaders();

    addCollapse();

    showFilters();

    sortColumn(find('.initial-sort'));

    findAll('.sortable').forEach(function(elem) {
        elem.addEventListener('click', function() {
            sortColumn(elem);
        }, false);
    });
}

function sortTable(table, clicked, keyFunc) {
    const rows = findAll('.results-table-row', table);
    const reversed = !clicked.classList.contains('asc');
    const sortedRows = sort(rows, keyFunc, reversed);

    const thead = find('.results-table-head', table);
    const tableCopy = table.cloneNode(deep=true);
    // Remove all rows except the header
    while (tableCopy.firstChild) {
        tableCopy.removeChild(tableCopy.lastChild);
    }

    tableCopy.appendChild(thead);
    sortedRows.forEach(function(elem) {
        tableCopy.appendChild(elem);
    });

    table.replaceWith(tableCopy);
}

function sort(items, keyFunc, reversed) {
    const sortArray = items.map(function(item, i) {
        return [keyFunc(item), i];
    });

    sortArray.sort(function(a, b) {
        const keyA = a[0];
        const keyB = b[0];

        if (keyA == keyB) return 0;

        if (reversed) {
            return keyA < keyB ? 1 : -1;
        } else {
            return keyA > keyB ? 1 : -1;
        }
    });

    return sortArray.map(function(item) {
        const index = item[1];
        return items[index];
    });
}

function keyAlpha(colIndex) {
    return function(elem) {
        return elem.childNodes[1].childNodes[colIndex].firstChild.data.toLowerCase();
    };
}

function keyLink(colIndex) {
    return function(elem) {
        const dataCell = elem.childNodes[1].childNodes[colIndex].firstChild;
        return dataCell == null ? '' : dataCell.innerText.toLowerCase();
    };
}

function keyResult(colIndex) {
    return function(elem) {
        const strings = ['Error', 'Failed', 'Rerun', 'XFailed', 'XPassed',
            'Skipped', 'Passed'];
        return strings.indexOf(elem.childNodes[1].childNodes[colIndex].firstChild.data);
    };
}

function resetSortHeaders(table) {
    findAll('.sort-icon', table).forEach(function(elem) {
        elem.parentNode.removeChild(elem);
    });
    findAll('.sortable', table).forEach(function(elem) {
        const icon = document.createElement('div');
        icon.className = 'sort-icon';
        icon.textContent = 'vvv';
        elem.insertBefore(icon, elem.firstChild);
        elem.classList.remove('desc', 'active');
        elem.classList.add('asc', 'inactive');
    });
}

function toggleSortStates(elem) {
    //if active, toggle between asc and desc
    if (elem.classList.contains('active')) {
        elem.classList.toggle('asc');
        elem.classList.toggle('desc');
    }

    const table = elem.parentNode.parentNode.parentNode;

    //if inactive, reset all other functions and add ascending active
    if (elem.classList.contains('inactive')) {
        resetSortHeaders(table);
        elem.classList.remove('inactive');
        elem.classList.add('active');
    }
}

function isAllRowsHidden(value) {
    return value.hidden == false;
}

function filterTable(elem) { // eslint-disable-line no-unused-vars
    const outcomeAtt = 'data-test-result';
    const outcome = elem.getAttribute(outcomeAtt);
    const classOutcome = outcome + ' results-table-row';
    const outcomeRows = document.getElementsByClassName(classOutcome);

    for(let i = 0; i < outcomeRows.length; i++){
        outcomeRows[i].hidden = !elem.checked;
    }

    findAll('.results-table').forEach(function(table) {
        const rows = findAll('.results-table-row', table).filter(isAllRowsHidden);
        const allRowsHidden = rows.length == 0 ? true : false;
        const notFoundMessage = find('.not-found-message', table);
        notFoundMessage.hidden = !allRowsHidden;
    });
}
