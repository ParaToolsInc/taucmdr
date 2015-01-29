var exports = module.exports;

var help   = require('../models/help');

exports.render = function(req, res) {
  var context = {};
  var template = __dirname + '/../views/help';
  res.render(template, context);
};
