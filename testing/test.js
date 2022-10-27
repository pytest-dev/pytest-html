/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/. */

if (!String.prototype.includes) {
    String.prototype.includes = function() {
        'use strict';
        return String.prototype.indexOf.apply(this, arguments) !== -1;
    };
}

QUnit.module( 'module', {
    beforeEach: function( assert ) {
        init();
    }
});

QUnit.test('sortColumn', function(assert){
    function sortColumnTest(colRe, firstElementThen, firstElementNow) {
        assert.equal(findAll('.results-table-row')[0].className, firstElementThen);
        const rowSort = find(colRe);
        sortColumn(rowSort);
        assert.equal(findAll('.results-table-row')[0].className, firstElementNow);
    }

    //check col-name, tests should be in this order test-1 => (test-2 => test-3) on col-name
    assert.equal(findAll('.col-name')[1].className, 'test-2 col-name');

    //result
    sortColumnTest('[col=result]',
        'rerun results-table-row', 'passed results-table-row');

    //make sure sorting the result column does not change the tests order in the col-name
    //tests should be in this order (test-2 => test-3) => test1 on col-name
    assert.equal(findAll('.col-name')[0].className, 'test-2 col-name');

    sortColumnTest('[col=result]',
        'passed results-table-row', 'rerun results-table-row');


    //name
    sortColumnTest('[col=name]',
        'rerun results-table-row', 'passed results-table-row');
    sortColumnTest('[col=name]',
        'passed results-table-row', 'rerun results-table-row');

    //duration
    sortColumnTest('[col=duration]',
        'rerun results-table-row', 'passed results-table-row');
    sortColumnTest('[col=duration]',
        'passed results-table-row', 'rerun results-table-row');

    //links
    sortColumnTest('[col=links]',
        'rerun results-table-row', 'passed results-table-row');
    sortColumnTest('[col=links]',
        'passed results-table-row', 'rerun results-table-row');
});

QUnit.test('filterTable', function(assert){
    function filterTableTest(outcome, checked) {
        const filterInput = document.createElement('input');
        filterInput.setAttribute('data-test-result', outcome);
        filterInput.checked = checked;
        filterTable(filterInput);

        const outcomes = findAll('.' + outcome);
        for(let i = 0; i < outcomes.length; i++) {
            assert.equal(outcomes[i].hidden, !checked);
        }
    }
    assert.true(find('#not-found-message').hidden);

    filterTableTest('rerun', false);
    filterTableTest('passed', false);
    assert.false(find('#not-found-message').hidden);

    filterTableTest('rerun', true);
    assert.true(find('#not-found-message').hidden);

    filterTableTest('passed', true);

});

QUnit.test('showHideExtras', function(assert) {
    function showExtrasTest(element){
        assert.equal(element.parentNode.nextElementSibling.className, 'collapsed');
        showExtras(element);
        assert.notEqual(element.parentNode.nextElementSibling.className, 'collapsed');
    }

    function hideExtrasTest(element){
        assert.notEqual(element.parentNode.nextElementSibling.className, 'collapsed');
        hideExtras(element);
        assert.equal(element.parentNode.nextElementSibling.className, 'collapsed');
    }
    //Passed results have log collapsed by default
    showExtrasTest(find('.passed').firstElementChild.firstElementChild);
    hideExtrasTest(find('.passed').firstElementChild.firstElementChild);

    hideExtrasTest(find('.rerun').firstElementChild.firstElementChild);
    showExtrasTest(find('.rerun').firstElementChild.firstElementChild);
});

QUnit.test('showHideAllExtras', function(assert) {
    function showAllExtrasTest(){
        showAllExtras();
        const extras = findAll('.extra');
        for (let i = 0; i < extras.length; i++) {
            assert.notEqual(extras[i].parentNode.className, 'collapsed');
        }
    }

    function hideAllExtrasTest(){
        hideAllExtras();
        const extras = findAll('.extra');
        for (let i = 0; i < extras.length; i++) {
            assert.equal(extras[i].parentNode.className, 'collapsed');
        }
    }

    showAllExtrasTest();
    hideAllExtrasTest();
});

QUnit.test('find', function (assert) {
    assert.notEqual(find('#results-table-head'), null);
    assert.notEqual(find('table#results-table'), null);
    assert.equal(find('.not-in-table'), null);
});

QUnit.test('findAll', function(assert) {
    assert.equal(findAll('.sortable').length, 4);
    assert.equal(findAll('.not-in-table').length, 0);
});
