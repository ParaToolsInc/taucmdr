var exports = module.exports;

var dashboard   = require('../models/dashboard');

exports.render = function(req, res) {
  var context = {};
  var template = __dirname + '/../views/dashboard';
  res.render(template, context);
};
