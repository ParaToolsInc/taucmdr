/**
* User.js
*
* @description :: TODO: You might write a short summary of how this model works and what it represents here.
* @docs        :: http://sailsjs.org/#!documentation/models
*/

module.exports = {

  schema: true,

  attributes: {
    username: { 
      type: 'string', 
      unique: true 
    },

    email: { 
      type: 'email',
      unique: true 
    },

    passports: { 
      collection: 'Passport', 
      via: 'user' 
    },

    projects: {
      collection: 'Project',
      via: 'user'
    },

    targets: {
      collection: 'Target',
      via: 'user'
    },

    applications: {
      collection: 'Application',
      via: 'user'
    },

    measurements: {
      collection: 'Measurement',
      via: 'user'
    },

    debuggers: {
      collection: 'Debugger',
      via: 'user'
    }

  }
};