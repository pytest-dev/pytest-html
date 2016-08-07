QUnit.test( "toArray", function(assert) {
  function NodeList() {}
  nodeList = new NodeList();
  assert.ok(toArray(nodeList) instanceof Array)
  assert.ok(toArray(null) === null)
});
