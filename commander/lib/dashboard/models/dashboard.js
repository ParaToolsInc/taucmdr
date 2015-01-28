var util = require('util');

function Dashboard() {}

Dashboard.prototype.welcomeMessage = function(argName) {
  var name = argName || "Stranger";
  return util.format('Hello %s! Welcome to TAU Commander!', name);  
};

// Typical CRUD

Dashboard.prototype.find = function(id) {
  // @TODO
};

Dashboard.prototype.save = function() {
  // @TODO
};

Dashboard.prototype.delete = function() {
  // @TODO
};

module.exports = new Dashboard();
