// http://ejohn.org/blog/ecmascript-5-strict-mode-json-and-more/
"use strict";

// Optional. You will see this name in eg. 'ps' or 'top' command
process.title = 'profile-rendering';

// Port where we'll run the websocket server
var webSocketsServerPort = 1337;

// websocket and http servers
var webSocketServer = require('websocket').server;
var http = require('http');

// Work around race condition between d3 and c3
var d3 = require("d3");
//var c3 = require("c3");

// Load fs module
var fs = require('fs');
// files in current directory
var fil;
// profile data
var prof = [];

/**
 * Helper function for escaping input strings
 */
function htmlEntities(str) {
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;')
                      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

/**
 * HTTP server
 */
var server = http.createServer(function(request, response) {
    // Not important for us. We're writing WebSocket server, not HTTP server
});
server.listen(webSocketsServerPort, function() {
    console.log((new Date()) + " Server is listening on port " + webSocketsServerPort);
});

/**
 * WebSocket server
 */
var wsServer = new webSocketServer({
    // WebSocket server is tied to a HTTP server. WebSocket request is just
    // an enhanced HTTP request. For more info http://tools.ietf.org/html/rfc6455#page-6
    httpServer: server
});

// This callback function is called every time someone
// tries to connect to the WebSocket server
wsServer.on('request', function(request) {
    console.log((new Date()) + ' Connection from origin ' + request.origin + '.');

    // accept connection - you should check 'request.origin' to make sure that
    // client is connecting from your website
    // (http://en.wikipedia.org/wiki/Same_origin_policy)
    var connection = request.accept(null, request.origin); 

    console.log((new Date()) + ' Connection accepted.');

    fil = fs.readdirSync(__dirname);
    var resultArray = fil.filter(function(d){
       var re = new RegExp("profile.*.*.*.json");
       return re.test(d);
    });
    
    prof = [];
    for(var i = 0; i < resultArray.length; i++){
       prof.push(fs.readFileSync(__dirname +'/'+ resultArray[i]).toString());
    }

    // send profile data
    if ( prof.length > 0) {
        connection.sendUTF(JSON.stringify( { type: 'profile', data: prof} ));
    }

    // user disconnected
    connection.on('close', function(connection) {
        console.log((new Date()) + " Peer "
            + connection.remoteAddress + " disconnected.");
    });

});
