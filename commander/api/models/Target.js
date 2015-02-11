/**
* Target.js
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

    // Projects this target belongs to
    projects: {
      collection: 'Project',
      via: 'targets'
    },

    // Target name
    name: {
      type: 'string',
      required: true
    },

    // Host OS
    host_os: {
      type: 'string',
      required: true
    },

    // Host architecture
    host_arch: {
      type: 'string',
      required: true
    },

    // Coprocessing device architecture
    device_arch: {
      type: 'string'
    },

    compilers: {
      collection: 'Compiler',
      via: 'target'
    },

    packages: {
      collection: 'Package',
      via: 'target'
    }

  }
};

