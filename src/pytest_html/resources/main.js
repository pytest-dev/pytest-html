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
    const colIndex = toArray(elem.parentNode.childNodes).indexOf(elem);
    let key;
    if (elem.classList.contains('result')) {
        key = keyResult;
    } else if (elem.classList.contains('links')) {
        key = keyLink;
    } else {
        key = keyAlpha;
    }
    sortTable(elem, key(colIndex));
}

function showAllExtras() { // eslint-disable-line no-unused-vars
    findAll('.col-result').forEach(showExtras);
}

function hideAllExtras() { // eslint-disable-line no-unused-vars
    findAll('.col-result').forEach(hideExtras);
}

function showExtras(colresultElem) {
    const extras = colresultElem.parentNode.nextElementSibling;
    const expandcollapse = colresultElem.firstElementChild;
    extras.classList.remove('collapsed');
    expandcollapse.classList.remove('expander');
    expandcollapse.classList.add('collapser');
}

function hideExtras(colresultElem) {
    const extras = colresultElem.parentNode.nextElementSibling;
    const expandcollapse = colresultElem.firstElementChild;
    extras.classList.add('collapsed');
    expandcollapse.classList.remove('collapser');
    expandcollapse.classList.add('expander');
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
    const resulttable = find('table#results-table');
    const showhideall = document.createElement('p');
    showhideall.innerHTML = '<a href="javascript:showAllExtras()">Show all details</a> / ' +
                            '<a href="javascript:hideAllExtras()">Hide all details</a>';
    resulttable.parentElement.insertBefore(showhideall, resulttable);

    // Add show/hide link to each result
    findAll('.col-result').forEach(function(elem) {
        const collapsed = getQueryParameter('collapsed') || 'Passed';
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
                showExtras(event.currentTarget);
            } else {
                hideExtras(event.currentTarget);
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
        elem.addEventListener('click',
            function() {
                sortColumn(elem);
            }, false);
    });

    var pieChart = new PieChart();
    pieChart.init();
}

function sortTable(clicked, keyFunc) {
    const rows = findAll('.results-table-row');
    const reversed = !clicked.classList.contains('asc');
    const sortedRows = sort(rows, keyFunc, reversed);
    /* Whole table is removed here because browsers acts much slower
     * when appending existing elements.
     */
    const thead = document.getElementById('results-table-head');
    document.getElementById('results-table').remove();
    const parent = document.createElement('table');
    parent.id = 'results-table';
    parent.appendChild(thead);
    sortedRows.forEach(function(elem) {
        parent.appendChild(elem);
    });
    document.getElementsByTagName('BODY')[0].appendChild(parent);
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

function resetSortHeaders() {
    findAll('.sort-icon').forEach(function(elem) {
        elem.parentNode.removeChild(elem);
    });
    findAll('.sortable').forEach(function(elem) {
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

    //if inactive, reset all other functions and add ascending active
    if (elem.classList.contains('inactive')) {
        resetSortHeaders();
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

    const rows = findAll('.results-table-row').filter(isAllRowsHidden);
    const allRowsHidden = rows.length == 0 ? true : false;
    const notFoundMessage = document.getElementById('not-found-message');
    notFoundMessage.hidden = !allRowsHidden;
}

var PieChart = function () {
    this.ctx = document.querySelector("canvas").getContext("2d");
    this.x0 = this.ctx.canvas.width / 2 + 60;
    this.y0 = this.ctx.canvas.height / 2;
    this.radius = 100;
    this.outLine = 20;
    this.spaceX=10;
    this.spaceY=20;
    this.smallW=30;
    this.smallH=15;
}

PieChart.prototype.init = function () {
    this.drawPie();
}

PieChart.prototype.drawPie = function () {
    var angleList = this.drawAngle();
    var start = 0;
    var colors = 'green,orange'.split(',');
    angleList.forEach(function (item, i) {
        var end = item.angle + start;
        this.ctx.beginPath();
        this.ctx.moveTo(this.x0, this.y0);
        this.ctx.arc(this.x0, this.y0, this.radius, start, end);
        this.ctx.fillStyle = colors[i];
        this.ctx.fill();
        this.drawTitle(start, item, this.ctx.fillStyle);
        this.drawInfo(i,item.title,this.ctx.fillStyle);
        start = end;
    }.bind(this));
}
PieChart.prototype.drawTitle = function (start, item, color) {
    var edge = this.radius + this.outLine;
    var edgeX = edge * Math.cos(start + item.angle / 2);
    var edgeY = edge * Math.sin(start + item.angle / 2);
    var outX = this.x0 + edgeX;
    var outY = this.y0 + edgeY;
    this.ctx.beginPath();
    this.ctx.moveTo(this.x0, this.y0);
    this.ctx.lineTo(outX, outY);
    this.ctx.strokeStyle = color;
    this.ctx.stroke();

    var align = outX > this.x0 ? "left" : "right";
    this.ctx.font = "15px Helvetica";
    this.ctx.textAlign = align;
    this.ctx.textBaseline = "bottom";
    this.ctx.fillStyle = color;
    this.ctx.fillText(item.title, outX, outY);

    var textW = this.ctx.measureText(item.title).width;
    this.ctx.moveTo(outX, outY);
    outX = outX > this.x0 ? outX + textW : outX - textW;
    this.ctx.lineTo(outX, outY);
    this.ctx.stroke();

}

PieChart.prototype.drawInfo = function (index,text,color) {
    this.ctx.beginPath();
    this.ctx.fillRect(this.spaceX,this.spaceY*index+this.smallH,this.smallW,this.smallH);
    this.ctx.font = "12px Helvetica";
    this.ctx.fillStyle = color;
    this.ctx.textAlign="left";
    this.ctx.fillText(text,this.spaceX*2+this.smallW,this.spaceY*index+this.smallH*2);
}

PieChart.prototype.drawAngle = function () {
    var total = 0;
    data.forEach(function (item, index) {
        total += item.num;
    });
    data.forEach(function (item, index) {
        var angle = item.num / total * Math.PI * 2;
        item.angle = angle;
    });
    return data;
}
