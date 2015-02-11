/**
* Measurement.js
*
* @description :: TODO: You might write a short summary of how this model works and what it represents here.
* @docs        :: http://sailsjs.org/#!documentation/models
*/

module.exports = {

  schema: true,

  attributes: {

    // One-to-many association
    user: {
      model: 'User', 
      required: true 
    },

    // Projects this measurement belongs to
    projects: {
      collection: 'Project',
      via: 'measurements'
    },

    // Target name
    name: {
      type: 'string',
      required: true
    },

    profile: {
      type: 'boolean',
      defaultsTo: true
    },

    trace: {
      type: 'boolean',
      defaultsTo: false
    },

    source_inst: {
      type: 'boolean',
      defaultsTo: true
    },

    // One of: [always, never, fallback]
    comp_inst: {
      type: 'string',
      defaultsTo: 'fallback'
    },

    sampling: {
      type: 'boolean',
      defaultsTo: false
    },

    io: {
      type: 'boolean',
      defaultsTo: false
    },

    memory: {
      type: 'boolean',
      defaultsTo: false
    }

  }
};

