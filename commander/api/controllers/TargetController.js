/**
 * TargetController
 *
 * @description :: Server-side logic for managing targets
 * @help        :: See http://links.sailsjs.org/docs/controllers
 */

module.exports = {

  new: function(req, res) {
    // Showing the edit view with !!target creates a new target
    res.locals.flash = _.clone(req.session.flash);
    res.view('target/edit');
    req.session.flash = {};
  },

  create: function(req, res) {
    Target.create(req.params.all(), function (err, created) {
      if (err) {
        console.log(err);
        req.session.flash = {
          err: err
        };
        return res.redirect('target/edit')
      }
      res.json(created);
      req.session.flash = {};
    });
  }

};