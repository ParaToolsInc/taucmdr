/**
* Application.js
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

    // Projects this application belongs to
    projects: {
      collection: 'Project',
      via: 'applications'
    },

    // Application name
    name: {
      type: 'string',
      required: true
    },

    version: {
      type: 'string',
    },

    source: {
      type: 'binary',
    },

    repo: {
      type: 'string',
    },

    openmp: {
      type: 'boolean',
      defaultsTo: false
    },

    pthreads: {
      type: 'boolean',
      defaultsTo: false
    },

    mpi: {
      type: 'boolean',
      defaultsTo: false
    },

    cuda: {
      type: 'boolean',
      defaultsTo: false
    },

    shmem: {
      type: 'boolean',
      defaultsTo: false
    },
    
    mpc: {
      type: 'boolean',
      defaultsTo: false
    }

  }
};

