/**
 * ProjectController
 *
 * @description :: Server-side logic for managing projects
 * @help        :: See http://links.sailsjs.org/docs/controllers
 */

 module.exports = {

  view: function(req, res, next) {
    Project.find({}).exec(function (err, projects) {
      if (err) {
        sails.log.error(err);
        return next(err);
      }
      if (!projects) {
        sails.log.debug('No projects found.');
        return next();
      }
      res.view({
        projects: projects
      });
    });
  },

  new: function(req, res, next) {
    res.view();
  },

  show: function(req, res, next) {
    var id = req.param('id');
    if (!id) return next();
    Project.findOne(id).exec(function (err, project) {
      if (err) {
        sails.log.error(err);
        return next(err);
      }
      if (!project) {
        sails.log.debug('Project ID '+id+' not found.');
        return next();
      }
      res.view({
        project: project
      });
    });
  },

  edit: function(req, res, next) {
    var id = req.param('id');
    if (!id) return next();
    Project.findOne(id).exec(function (err, project) {
      if (err) {
        sails.log.error(err);
        return next(err);
      }
      if (!project) {
        sails.log.debug('Project ID '+id+' not found.');
        return next();
      }
      res.view({
        project: project
      });
    });
  },

  create: function(req, res, next) {
    Project.create(req.params.all()).exec(function (err, project) {
      if (err) {
        sails.log.error(err);
        return next(err);
      }
      res.redirect('/project');
    });
  },

  update: function(req, res, next) {
    var id = req.param('id');
    if (!id) return next();
    Project.update({id: id}, req.params.all()).exec(function (err, project) {
      if (err) {
        sails.log.error(err);
        return next(err);
      }
      if (!project) {
        sails.log.debug('Project ID '+id+' not found.');
        return next();
      }
      res.redirect('/project/show/'+id);
    });
  },

  destroy: function(req, res, next) {
    var id = req.param('id');
    if (!id) return next();
    Project.destroy({id: id}).exec(function (err) {
      if (err) {
        sails.log.error(err);
        return next(err);
      }
      res.redirect('/project');
    });
  }

};