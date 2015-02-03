/**
 * sessionAuth
 *
 * @module      :: Policy
 * @description :: Simple policy to allow any authenticated user
 *                 Assumes that your login action in one of your controllers sets `req.session.authenticated = true;`
 * @docs        :: http://sailsjs.org/#!documentation/policies
 *
 */
module.exports = function(req, res, next) {

  if (req.user) return next();

  // If this is not an HTML-wanting browser, e.g. AJAX/sockets/cURL/etc.,
  // send a 401 response letting the user agent know they need to login to
  // access this endpoint.
  if (req.wantsJSON) {
    return res.forbidden('You are not permitted to perform this action.');
  }

  // Otherwise if this is an HTML-wanting browser, do a redirect.
  return res.redirect('/login');

  // // User is not allowed
  // // (default res.forbidden() behavior can be overridden in `config/403.js`)
  // return res.forbidden('You are not permitted to perform this action.');
};
