var exports = module.exports;

var analysis = require('../models/analysis');

exports.render = function(req, res) {
  var context = {};
  var template = __dirname + '/../views/analysis';
  res.render(template, context);
};
