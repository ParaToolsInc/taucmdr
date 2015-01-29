var exports = module.exports;

var projects = require('../models/projects');

exports.render = function(req, res) {
  var context = {};
  var template = __dirname + '/../views/projects';
  res.render(template, context);
};
