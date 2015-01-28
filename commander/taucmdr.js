require('nodebootstrap-server').setup(function(runningApp) {
  var consolidate = require('consolidate');

  runningApp.set('view engine', 'dust');
  runningApp.engine('dust', consolidate.dust);

  //---- Mounting well-encapsulated application modules
  //---- See: http://vimeo.com/56166857

  runningApp.use('/hello', require('hello')); // attach to sub-route
  runningApp.use('/dashboard', require('dashboard')); // attach to sub-route
  runningApp.use(require('routes')); // attach to root route

});
