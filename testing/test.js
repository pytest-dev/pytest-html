/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this file,
 * You can obtain one at http://mozilla.org/MPL/2.0/. */

//Mocks
function NodeList() {}

function create_elem_table() {
  var table = document.createElement('table');
  table.id = 'results-table'

  //head
  var thead = table.createTHead();
  thead.id = 'results-table-head'
  var head_row = thead.insertRow(0);
  //result column
  var result = head_row.insertCell(0);
  result.className = 'sortable initial-sort result asc active';
  result.setAttribute('col', 'result');
  result.innerHTML = '<div class="sort-icon">vvv</div> Result';
  //test column
  var test = head_row.insertCell(1);
  test.className = 'sortable asc active';
  test.setAttribute('col', 'name');
  test.innerHTML = '<div class="sort-icon">vvv</div> Test';
  //duration column
  var duration = head_row.insertCell(2);
  duration.className = 'sortable numeric asc active';
  duration.setAttribute('col', 'duration');
  duration.innerHTML = '<div class="sort-icon">vvv</div> Duration';
  //Links
  var links = head_row.insertCell(3);
  links.innerHTML = "Links";

  //Failed row
  var tbody_failed = document.createElement('tbody');
  tbody_failed.className = 'failed results-table-row';
  //columns
  var failed_row = tbody_failed.insertRow(0);
  var col_result_failed = failed_row.insertCell(0);
  col_result_failed.className = 'col-result';
  col_result_failed.innerHTML = 'Failed';
  var col_name_failed = failed_row.insertCell(1);
  col_name_failed.className = 'col-name';
  col_name_failed.innerHTML = 'test_documentation.py::test_fail';
  var col_duration_failed = failed_row.insertCell(2);
  col_duration_failed.className = 'col-duration';
  col_duration_failed.innerHTML = '0.00';
  var col_links_failed = failed_row.insertCell(3);
  col_links_failed.className = 'col-links';
  // extra and log
  var row_extra_failed = tbody_failed.insertRow(0);
  var col_extra_failed = row_extra_failed.insertCell(0);
  col_extra_failed.className = 'extra';
  col_extra_failed.innerHTML = '<div class="log"></div>';

  table.appendChild(thead);
  table.appendChild(tbody_failed);
  return table;
}

QUnit.test( 'toArray', function(assert) {
  var nodeList = new NodeList();
  assert.ok(toArray(nodeList) instanceof Array);
  assert.ok(toArray(null) === null);
});

QUnit.test('find', function (assert) {
  var table = create_elem_table();
  assert.ok(find('thead', table).innerText ===
            'vvv Resultvvv Testvvv DurationLinks');
  assert.ok(find('.sort-icon', table).innerHTML === 'vvv');
});

QUnit.test('find_all', function(assert) {
  var table = create_elem_table();
  assert.ok(find_all('.sort-icon', table).length === 3);
});
