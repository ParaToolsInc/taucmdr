// Third party libraries
var express = require('express')
  , app = exports = module.exports = express();

// Local includes
var dashboard = require('./dashboard');

// Global routes
app.get('/', dashboard.callbacks.render);
