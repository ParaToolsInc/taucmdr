/**
 * ProjectController
 *
 * @description :: Server-side logic for managing projects
 * @help        :: See http://links.sailsjs.org/docs/controllers
 */

module.exports = {

	/**
   * Render projects view
   *
   * @param {Object} req
   * @param {Object} res
   */
  main: function (req, res) {
    res.view('project/main');
  }
	
};

