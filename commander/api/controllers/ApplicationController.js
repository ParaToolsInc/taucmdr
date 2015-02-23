/**
 * ApplicationController
 *
 * @description :: Server-side logic for managing applications
 * @help        :: See http://links.sailsjs.org/docs/controllers
 */

 module.exports = {

  view: function(req, res, next) {
    Application.find({}).exec(function (err, applications) {
      if (err) {
        sails.log.error(err);
        return next(err);
      }
      if (!applications) {
        sails.log.debug('No applications found.');
        return next();
      }
      res.view({
        applications: applications
      });
    });
  },

  new: function(req, res, next) {
    res.view();
  },

  show: function(req, res, next) {
    var id = req.param('id');
    if (!id) return next();
    Application.findOne(id).exec(function (err, application) {
      if (err) {
        sails.log.error(err);
        return next(err);
      }
      if (!application) {
        sails.log.debug('Application ID '+id+' not found.');
        return next();
      }
      res.view({
        application: application
      });
    });
  },

  edit: function(req, res, next) {
    var id = req.param('id');
    if (!id) return next();
    Application.findOne(id).exec(function (err, application) {
      if (err) {
        sails.log.error(err);
        return next(err);
      }
      if (!application) {
        sails.log.debug('Application ID '+id+' not found.');
        return next();
      }
      res.view({
        application: application
      });
    });
  },

  create: function(req, res, next) {
    Application.create(req.params.all()).exec(function (err, application) {
      if (err) {
        sails.log.error(err);
        return next(err);
      }
      res.redirect('/application');
    });
  },

  update: function(req, res, next) {
    var id = req.param('id');
    if (!id) return next();
    Application.update({id: id}, req.params.all()).exec(function (err, application) {
      if (err) {
        sails.log.error(err);
        return next(err);
      }
      if (!application) {
        sails.log.debug('Application ID '+id+' not found.');
        return next();
      }
      res.redirect('/application/show/'+id);
    });
  },

  destroy: function(req, res, next) {
    var id = req.param('id');
    if (!id) return next();
    Application.destroy({id: id}).exec(function (err) {
      if (err) {
        sails.log.error(err);
        return next(err);
      }
      res.redirect('/application');
    });
  }

};