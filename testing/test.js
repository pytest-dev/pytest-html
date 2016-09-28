/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/. */

 QUnit.module( 'module', {
   beforeEach: function( assert ) {
      init();
    }
  });

 QUnit.test('sort_column', function(assert){
   function sort_column_test(col_re, first_element_then, first_element_now) {
     assert.equal(find_all('.results-table-row')[0].className, first_element_then);
     var row_sort = find(col_re);
     sort_column(row_sort);
     assert.equal(find_all('.results-table-row')[0].className, first_element_now);
   }
   //result
   sort_column_test('[col=result]',
                    'rerun results-table-row', 'passed results-table-row');
   sort_column_test('[col=result]',
                    'passed results-table-row', 'rerun results-table-row');

   //name
   sort_column_test('[col=name]',
                    'rerun results-table-row', 'passed results-table-row');
   sort_column_test('[col=name]',
                    'passed results-table-row', 'rerun results-table-row');

   //numeric
   sort_column_test('[col=duration]',
                    'rerun results-table-row', 'passed results-table-row');
   sort_column_test('[col=duration]',
                    'passed results-table-row', 'rerun results-table-row');
 });

QUnit.test('filter_table', function(assert){
  function filter_table_test(outcome, checked) {
    var filter_input = document.createElement('input');
    filter_input.setAttribute('data-test-result', outcome);
    filter_input.checked = checked;
    filter_table(filter_input);

    var outcomes = find_all('.' + outcome);
    for(var i = 0; i < outcomes.length; i++) {
      assert.equal(outcomes[i].hidden, !checked);
    }
  }
  assert.equal(find('#not-found-message').hidden, true);

  filter_table_test('rerun', false);
  filter_table_test('passed', false);
  assert.equal(find('#not-found-message').hidden, false);

  filter_table_test('rerun', true);
  assert.equal(find('#not-found-message').hidden, true);

  filter_table_test('passed', true);

});

QUnit.test('show_hide_extras', function(assert) {
  function show_extras_test(element){
    assert.equal(element.parentNode.nextElementSibling.className, 'collapsed');
    show_extras(element);
    assert.notEqual(element.parentNode.nextElementSibling.className, 'collapsed');
  }

  function hide_extras_test(element){
    assert.notEqual(element.parentNode.nextElementSibling.className, 'collapsed');
    hide_extras(element);
    assert.equal(element.parentNode.nextElementSibling.className, 'collapsed');
  }
  //Passed results have log collapsed by default
  show_extras_test(find('.passed').firstElementChild.firstElementChild);
  hide_extras_test(find('.passed').firstElementChild.firstElementChild);

  hide_extras_test(find('.rerun').firstElementChild.firstElementChild);
  show_extras_test(find('.rerun').firstElementChild.firstElementChild);
});

QUnit.test('show_hide_all_extras', function(assert) {
  function show_all_extras_test(){
    show_all_extras();
    var extras = find_all('.extra');
    for (var i = 0; i < extras.length; i++) {
      assert.notEqual(extras[i].parentNode.className, 'collapsed');
    }
  }

  function hide_all_extras_test(){
    hide_all_extras();
    var extras = find_all('.extra');
    for (var i = 0; i < extras.length; i++) {
      assert.equal(extras[i].parentNode.className, 'collapsed');
    }
  }

  show_all_extras_test();
  hide_all_extras_test();
});

QUnit.test('find', function (assert) {
  assert.notEqual(find('#results-table-head'), null);
  assert.notEqual(find('table#results-table'), null);
  assert.equal(find('.not-in-table'), null);
});

QUnit.test('find_all', function(assert) {
  assert.equal(find_all('.sortable').length, 3);
  assert.equal(find_all('.not-in-table').length, 0);
});
