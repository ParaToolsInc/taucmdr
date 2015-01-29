require('nodebootstrap-server').setup(function(runningApp) {
  var consolidate = require('consolidate');

  runningApp.set('view engine', 'dust');
  runningApp.engine('dust', consolidate.dust);

  //---- Mounting well-encapsulated application modules
  //---- See: http://vimeo.com/56166857

  // attach sub-routes
  runningApp.use('/dashboard', require('dashboard'));
  runningApp.use('/projects', require('projects'));
  runningApp.use('/targets', require('targets'));
  runningApp.use('/analysis', require('analysis'));
  runningApp.use('/help', require('help'));

  // attach root route
  runningApp.use(require('routes'));

});
