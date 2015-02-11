/**
* Debugger.js
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

    // Projects this debugger belongs to
    projects: {
      collection: 'Project',
      via: 'debuggers'
    },

    // Target name
    name: {
      type: 'string',
      required: true
    },

    callstack: {
      type: 'boolean',
      defaultsTo: true
    },

    memory: {
      type: 'boolean',
      defaultsTo: false
    }

  }
};

