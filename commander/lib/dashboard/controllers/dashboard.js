var exports = module.exports;

var dashboard = require('../models/dashboard');

exports.renderDashboard = function(req, res) {

  var name = req.query.name || "";

  var context = {
    title: "TAU Commander Dashboard"
  , welcomeMessage: dashboard.welcomeMessage(name)
  };

  var template = __dirname + '/../views/dashboard';
  res.render(template, context);
};
