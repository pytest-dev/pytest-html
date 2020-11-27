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

function find_all(selector, elem) {
    if (!elem) {
        elem = document;
    }
    return toArray(elem.querySelectorAll(selector));
}

function sort_column(elem) {
    toggle_sort_states(elem);
    const colIndex = toArray(elem.parentNode.childNodes).indexOf(elem);
    let key;
    if (elem.classList.contains('numeric')) {
        key = key_num;
    } else if (elem.classList.contains('result')) {
        key = key_result;
    } else if (elem.classList.contains('links')) {
        key = key_link;
    } else {
        key = key_alpha;
    }
    sort_table(elem, key(colIndex));
}

function show_all_extras() { // eslint-disable-line no-unused-vars
    find_all('.col-result').forEach(show_extras);
}

function hide_all_extras() { // eslint-disable-line no-unused-vars
    find_all('.col-result').forEach(hide_extras);
}

function show_extras(colresult_elem) {
    const extras = colresult_elem.parentNode.nextElementSibling;
    const expandcollapse = colresult_elem.firstElementChild;
    extras.classList.remove('collapsed');
    expandcollapse.classList.remove('expander');
    expandcollapse.classList.add('collapser');
}

function hide_extras(colresult_elem) {
    const extras = colresult_elem.parentNode.nextElementSibling;
    const expandcollapse = colresult_elem.firstElementChild;
    extras.classList.add('collapsed');
    expandcollapse.classList.remove('collapser');
    expandcollapse.classList.add('expander');
}

function show_filters() {
    const filter_items = document.getElementsByClassName('filter');
    for (let i = 0; i < filter_items.length; i++)
        filter_items[i].hidden = false;
}

function add_collapse() {
    // Add links for show/hide all
    const resulttable = find('table#results-table');
    const showhideall = document.createElement('p');
    showhideall.innerHTML = '<a href="javascript:show_all_extras()">Show all details</a> / ' +
                            '<a href="javascript:hide_all_extras()">Hide all details</a>';
    resulttable.parentElement.insertBefore(showhideall, resulttable);

    // Add show/hide link to each result
    find_all('.col-result').forEach(function(elem) {
        const collapsed = get_query_parameter('collapsed') || 'Passed';
        const extras = elem.parentNode.nextElementSibling;
        const expandcollapse = document.createElement('span');
        if (extras.classList.contains('collapsed')) {
            expandcollapse.classList.add('expander');
        } else if (collapsed.includes(elem.innerHTML)) {
            extras.classList.add('collapsed');
            expandcollapse.classList.add('expander');
        } else {
            expandcollapse.classList.add('collapser');
        }
        elem.appendChild(expandcollapse);

        elem.addEventListener('click', function(event) {
            if (event.currentTarget.parentNode.nextElementSibling.classList.contains('collapsed')) {
                show_extras(event.currentTarget);
            } else {
                hide_extras(event.currentTarget);
            }
        });
    });
}

function get_query_parameter(name) {
    const match = RegExp('[?&]' + name + '=([^&]*)').exec(window.location.search);
    return match && decodeURIComponent(match[1].replace(/\+/g, ' '));
}

function init () { // eslint-disable-line no-unused-vars
    reset_sort_headers();

    add_collapse();

    show_filters();

    sort_column(find('.initial-sort'));

    find_all('.sortable').forEach(function(elem) {
        elem.addEventListener('click',
            function() {
                sort_column(elem);
            }, false);
    });
}

function sort_table(clicked, key_func) {
    const rows = find_all('.results-table-row');
    const reversed = !clicked.classList.contains('asc');
    const sorted_rows = sort(rows, key_func, reversed);
    /* Whole table is removed here because browsers acts much slower
     * when appending existing elements.
     */
    const thead = document.getElementById('results-table-head');
    document.getElementById('results-table').remove();
    const parent = document.createElement('table');
    parent.id = 'results-table';
    parent.appendChild(thead);
    sorted_rows.forEach(function(elem) {
        parent.appendChild(elem);
    });
    document.getElementsByTagName('BODY')[0].appendChild(parent);
}

function sort(items, key_func, reversed) {
    const sort_array = items.map(function(item, i) {
        return [key_func(item), i];
    });

    sort_array.sort(function(a, b) {
        const key_a = a[0];
        const key_b = b[0];

        if (key_a == key_b) return 0;

        if (reversed) {
            return key_a < key_b ? 1 : -1;
        } else {
            return key_a > key_b ? 1 : -1;
        }
    });

    return sort_array.map(function(item) {
        const index = item[1];
        return items[index];
    });
}

function key_alpha(col_index) {
    return function(elem) {
        return elem.childNodes[1].childNodes[col_index].firstChild.data.toLowerCase();
    };
}

function key_num(col_index) {
    return function(elem) {
        return parseFloat(elem.childNodes[1].childNodes[col_index].firstChild.data);
    };
}

function key_link(col_index) {
    return function(elem) {
        const dataCell = elem.childNodes[1].childNodes[col_index].firstChild;
        return dataCell == null ? '' : dataCell.innerText.toLowerCase();
    };
}

function key_result(col_index) {
    return function(elem) {
        const strings = ['Error', 'Failed', 'Rerun', 'XFailed', 'XPassed',
            'Skipped', 'Passed'];
        return strings.indexOf(elem.childNodes[1].childNodes[col_index].firstChild.data);
    };
}

function reset_sort_headers() {
    find_all('.sort-icon').forEach(function(elem) {
        elem.parentNode.removeChild(elem);
    });
    find_all('.sortable').forEach(function(elem) {
        const icon = document.createElement('div');
        icon.className = 'sort-icon';
        icon.textContent = 'vvv';
        elem.insertBefore(icon, elem.firstChild);
        elem.classList.remove('desc', 'active');
        elem.classList.add('asc', 'inactive');
    });
}

function toggle_sort_states(elem) {
    //if active, toggle between asc and desc
    if (elem.classList.contains('active')) {
        elem.classList.toggle('asc');
        elem.classList.toggle('desc');
    }

    //if inactive, reset all other functions and add ascending active
    if (elem.classList.contains('inactive')) {
        reset_sort_headers();
        elem.classList.remove('inactive');
        elem.classList.add('active');
    }
}

function is_all_rows_hidden(value) {
    return value.hidden == false;
}

function filter_table(elem) { // eslint-disable-line no-unused-vars
    const outcome_att = 'data-test-result';
    const outcome = elem.getAttribute(outcome_att);
    const class_outcome = outcome + ' results-table-row';
    const outcome_rows = document.getElementsByClassName(class_outcome);

    for(let i = 0; i < outcome_rows.length; i++){
        outcome_rows[i].hidden = !elem.checked;
    }

    const rows = find_all('.results-table-row').filter(is_all_rows_hidden);
    const all_rows_hidden = rows.length == 0 ? true : false;
    const not_found_message = document.getElementById('not-found-message');
    not_found_message.hidden = !all_rows_hidden;
}
