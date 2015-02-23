/**
 * TargetController
 *
 * @description :: Server-side logic for managing targets
 * @help        :: See http://links.sailsjs.org/docs/controllers
 */

 module.exports = {

  view: function(req, res, next) {
    Target.find({}).exec(function (err, targets) {
      if (err) {
        sails.log.error(err);
        return next(err);
      }
      if (!targets) {
        sails.log.warn('No targets found.');
        return next();
      }
      res.view({
        targets: targets
      });
    });
  },

  new: function(req, res, next) {
    res.view();
  },

  show: function(req, res, next) {
    var id = req.param('id');
    if (!id) return next();
    Target.findOne(id).exec(function (err, target) {
      if (err) {
        sails.log.error(err);
        return next(err);
      }
      if (!target) {
        sails.log.warn('Target ID '+id+' not found.');
        return next();
      }
      res.view({
        target: target
      });
    });
  },

  edit: function(req, res, next) {
    var id = req.param('id');
    if (!id) return next();
    Target.findOne(id).exec(function (err, target) {
      if (err) {
        sails.log.error(err);
        return next(err);
      }
      if (!target) {
        sails.log.warn('Target ID '+id+' not found.');
        return next();
      }
      res.view({
        target: target
      });
    });
  },

  create: function(req, res, next) {
    Target.create(req.params.all()).exec(function (err, target) {
      if (err) {
        sails.log.error(err);
        return next(err);
      }
      res.redirect('/target');
    });
  },

  update: function(req, res, next) {
    var id = req.param('id');
    if (!id) return next();
    Target.update({id: id}, req.params.all()).exec(function (err, target) {
      if (err) {
        sails.log.error(err);
        return next(err);
      }
      if (!target) {
        sails.log.warn('Target ID '+id+' not found.');
        return next();
      }
      res.redirect('/target/show/'+id);
    });
  },

  destroy: function(req, res, next) {
    var id = req.param('id');
    if (!id) return next();
    Target.destroy({id: id}).exec(function (err) {
      if (err) {
        sails.log.error(err);
        return next(err);
      }
      res.redirect('/target');
    });
  }

};