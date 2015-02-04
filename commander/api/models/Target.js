/**
* Target.js
*
* @description :: TODO: You might write a short summary of how this model works and what it represents here.
* @docs        :: http://sailsjs.org/#!documentation/models
*/

module.exports = {

  schema: true,

  attributes: {

    name: {
      type: 'string',
      required: true
    },

    user: {
      model: 'User', 
      required: true 
    },

    // toJSON: function() {
    //   var obj = this.toObject();
    //   delete obj._csrf;
    //   delete obj.toJSON;
    //   return obj;
    // }

  }
};

