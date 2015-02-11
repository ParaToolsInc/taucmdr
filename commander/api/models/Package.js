/**
* Package.js
*
* @description :: TODO: You might write a short summary of how this model works and what it represents here.
* @docs        :: http://sailsjs.org/#!documentation/models
*/

module.exports = {

  schema: true,

  attributes: {

    // One-to-many association
    target: {
      model: 'Target', 
      required: true 
    },

    // Package name, e.g. 'OpenMPI'
    name: {
      type: 'string',
      required: true
    },

    cflags: {
      type: 'string'
    },

    cxxflags: {
      type: 'string'
    },

    fflags: {
      type: 'string'
    },

    ldflags: {
      type: 'string'
    },

    libs: {
      type: 'string'
    }

  }
};

