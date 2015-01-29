var exports = module.exports;

var targets   = require('../models/targets');

exports.render = function(req, res) {
  var context = {};
  var template = __dirname + '/../views/targets';
  res.render(template, context);
};
