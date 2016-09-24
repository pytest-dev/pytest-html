/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/. */

 QUnit.module( "module", {
   beforeEach: function( assert ) {
      init();
    }
  });

 QUnit.test('sort_column', function(assert){
   function sort_column_test(parameter, first_element_then, first_element_now) {
     assert.ok(find_all('.results-table-row')[0].className == first_element_then);
     var row_sort = find(parameter);
     sort_column(row_sort);
     assert.ok(find_all('.results-table-row')[0].className == first_element_now);
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

QUnit.test('find', function (assert) {
  assert.ok(find('#results-table-head') != null);
  assert.ok(find('table#results-table') != null);
  assert.ok(find('.not-in-table') === null);
});

QUnit.test('find_all', function(assert) {
  assert.ok(find_all('.sortable').length === 3);
  assert.ok(find_all('.not-in-table').length === 0);
});
