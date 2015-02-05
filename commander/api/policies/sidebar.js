/**
 * sidebar
 *
 * @module      :: Policy
 * @description :: Provides sidebar items
 * @docs        :: http://sailsjs.org/#!documentation/policies
 *
 */
module.exports = function(req, res, next) {
  var sidebar_items = [
    {title: 'Projects', href: '/project', icon: 'glyphicon-ok-circle'},
    {title: 'Applications', href: '/application', icon: 'glyphicon-modal-window'},
    {title: 'Targets', href: '/target', icon: 'glyphicon-screenshot'},
    {title: 'Analysis', href: '/analysis', icon: 'glyphicon-stats'},
    {title: 'Help', href: '/help', icon: 'glyphicon-question-sign'},
  ];

  for (i=0; i<sidebar_items.length; i++) {
    sidebar_items[i].active = (req.path.indexOf(sidebar_items[i].href) == 0);
  }
  res.locals.sidebar_items = sidebar_items;
  return next();
};
