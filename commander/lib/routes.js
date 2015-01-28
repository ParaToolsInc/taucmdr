// Third party libraries
var express = require('express')
  , exports = module.exports = express()
  , app = exports;

// Local includes
var dashboard = require('./dashboard');

// Global routes
app.get('/', dashboard.callbacks.renderDashboard);
