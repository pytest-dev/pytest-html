module.exports = function(grunt) {
  grunt.initConfig({
    qunit: {
      src: 'testing/js_test_report.html'
    }
  });
  grunt.loadNpmTasks('grunt-contrib-qunit');
  grunt.registerTask('test', 'qunit:src');
};
