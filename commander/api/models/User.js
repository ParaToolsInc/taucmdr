/**
* User.js
*
* @description :: TODO: You might write a short summary of how this model works and what it represents here.
* @docs        :: http://sailsjs.org/#!documentation/models
*/

module.exports = {

  attributes: {

    email: {
      type: 'string'
    },

    name: {
      type: 'string'
    },

    password: {
      type: 'string'
    },

    targets: {
      collection: 'target',
      via: 'owner'
    },

    projects: {
      collection: 'project',
      via: 'owner'
    }

  }
};

