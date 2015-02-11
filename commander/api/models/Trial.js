/**
* Trial.js
*
* @description :: TODO: You might write a short summary of how this model works and what it represents here.
* @docs        :: http://sailsjs.org/#!documentation/models
*/

module.exports = {

  schema: true,

  attributes: {

    // The project this trial belongs to
    project: {
      model: 'Project',
      required: true
    },

    // The target used in this trial
    target: {
      model: 'Target',
      required: true
    },

    // The application used in this trial
    application: {
      model: 'Application',
      required: true
    },

    // The measurement used in this trial
    measurement: {
      model: 'Measurement',
      required: true
    },

    // The debugger used in this trial
    debugger: {
      model: 'Debugger',
      required: true
    },

    // The result of this trial
    result: {
      type: 'binary'
    }

  }
};

