//var util = require('util');

function Projects() {}

/*
Projects.prototype.welcomeMessage = function(argName) {
  var name = argName || "Stranger";
  return util.format('Hello %s! Welcome to TAU Commander!', name);  
};
*/

// Typical CRUD

Projects.prototype.find = function(id) {
  // @TODO
};

Projects.prototype.save = function() {
  // @TODO
};

Projects.prototype.delete = function() {
  // @TODO
};

module.exports = new Projects();
