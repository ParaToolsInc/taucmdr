/**
 * DashboardController
 *
 * @description :: Server-side logic for managing dashboards
 * @help        :: See http://links.sailsjs.org/docs/controllers
 */

module.exports = {

  /**
   * Render the dashboard
   *
   * @param {Object} req
   * @param {Object} res
   */
  main: function (req, res) {
    res.view('dashboard/main');
  }

};

