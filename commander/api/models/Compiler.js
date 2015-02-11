/**
* Compiler.js
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

    // Compiler language
    language: {
      type: 'string',
      required: true
    },

    // Compiler family name, e.g. 'intel'
    family_name: {
      type: 'string',
      required: true
    },

    // Compiler version
    version: {
      type: 'string',
      required: true
    },

    // Compiler command
    command: {
      type: 'string',
      required: true
    },

    // MD5 sum of compiler exe
    command_md5: {
      type: 'string',
      required: true
    }

  }
};

