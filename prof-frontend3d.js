$(function () {
    "use strict";

    // for better performance - to avoid searching in DOM
    var content = $('#content');
    var input = $('#input');
    var status = $('#status');
    var split = $('#split');

    // if user is running mozilla then use it's built-in WebSocket
    window.WebSocket = window.WebSocket || window.MozWebSocket;

    // if browser doesn't support WebSocket, just show some notification and exit
    if (!window.WebSocket) {
        content.html($('<p>', { text: 'Sorry, but your browser doesn\'t '
                                    + 'support WebSockets.'} ));
        input.hide();
        $('span').hide();
        return;
    }

    // open connection
    var connection = new WebSocket('ws://127.0.0.1:1337');

    connection.onopen = function () {
        // first we want users to enter their names
        input.removeAttr('disabled');
        status.text('Choose name:');
    };

    $(window).on('beforeunload', function(){
        connection.close();
    });

    connection.onerror = function (error) {
        // just in there were some problems with conenction...
        content.html($('<p>', { text: 'Sorry, but there\'s some problem with your '
                                    + 'connection or the server is down.' } ));
    };

    // most important part - incoming messages
    connection.onmessage = function (message) {
        // try to parse JSON message. Because we know that the server always returns
        // JSON this should work without any problem but we should make sure that
        // the massage is not chunked or otherwise damaged.
        try {
            var json = JSON.parse(message.data);
        } catch (e) {
            console.log('This doesn\'t look like a valid JSON: ', message.data);
            return;
        }

        // NOTE: if you're not sure about the JSON structure
        // check the server source code above
        if ( json.type == 'profile') {// entire profile data

            var profJson = JSON.parse(json.data[0]);

            //var metrics = ["Exclusive", "Inclusive", "Subroutines", "Calls"];
            var metrics = [];
            for(var i = 0;i<profJson.length;i++)
            {
                Object.keys(profJson[i]).forEach(function(key){
                    if(metrics.indexOf(key) == -1 && key != "node" && key != "thread" && key != "Function Name")
                    {
                        metrics.unshift(key);
                    }
                });
            }
            var metric = metrics[0];
	    make3dVis(json, metric);

            var selectUI = d3.select("#droplist_metric")
                     .append("select")
                     .attr("id", "Metrics")
                     .selectAll("option")
                     .data(d3.values(metrics))
                     .enter().append("option")
                     .attr("value", function(d) { return d;})
                     .text(function(d) { return d;});
            var checkOption = function (e) {
                    if(e === metric){
                        return d3.select(this).attr("selected", "selected");
                    }
            };
            selectUI.selectAll("option").each(checkOption);
            d3.select('select').on("change", function() {
               var key = this.value;
               metric = key;
	       make3dVis(json, metric);
            });



        } else {
            console.log('Hmm..., I\'ve never seen JSON like this: ', json);
        }
    };

    /**
     * This method is optional. If the server wasn't able to respond to the
     * in 3 seconds then show some error message to notify the user that
     * something is wrong.
     */
    setInterval(function() {
        if (connection.readyState !== 1) {
            status.text('Error');
            input.attr('disabled', 'disabled').val('Unable to comminucate '
                                                 + 'with the WebSocket server.');
        }
    }, 3000);

	function make3dview( prof )
	{
		/* Create a thread array each thread with the following data
		 * {
		 * 		node : NID,
		 * 		threadid: ID,
		 * 		profile : []
		 * }
		 */

		var streams = [];
		
		/* We need to store functions
		 * at the same offset */
		var func_id = 0;
		var funclut = {};

		for( var p = 0 ; p < prof.data.length ; p++ )
		{
			var perthreadprof = JSON.parse( prof.data[p] );
			
			var newstream = {};
			
			newstream.node = perthreadprof[0].node;
			newstream.thread = perthreadprof[0].thread;
			newstream.profile = [];
			
			for( var k = 1 ; k < perthreadprof.length ; k++ )
			{
				/* Make sure that functions already encountered are
				 * at the same offset */
				var functoffset = 0;
				var funcname = perthreadprof[k]["Function Name"];

				if( funclut[ funcname  ] )
				{
					functoffset = funclut[  funcname ] ;
				}
				else
				{
					functoffset = func_id++;
					funclut[ funcname ] = functoffset;
				}
				
				newstream.profile[functoffset] =  perthreadprof[k];
			}
			
			streams.push( newstream );
		}

		return streams;
	}


	function make3dVis(prof, metric)
	{
		var streams = make3dview(prof);
                var data = null;
                var graph = null;
		var funcNames=[];
       
                // Called when the Visualization API is loaded.
                // Create and populate a data table.
                var options = {};
                var data = new vis.DataSet(options);
		//var metric = "Exclusive (msec)";
		var maxVal = 0;
		//var zvals = [];

		  for(var i = 0; i < streams.length; i++) {
			  for(var j = 0; j < streams[i]["profile"].length; j++) {
			      if(streams[i]["profile"][j])
			      {
			  	data.add({
					x: i,
					y: j,
					z: streams[i]["profile"][j][metric],
					style: streams[i]["profile"][j][metric]
				});
				funcNames[j] = streams[i]["profile"][j]["Function Name"];
				//zvals.push(streams[i]["profile"][j][metric]);
				if(maxVal < streams[i]["profile"][j][metric])
				{
					maxVal = streams[i]["profile"][j][metric];
				}
			      }
			      else
			      {
			  	data.add({
					x: i,
					y: j,
					z: 0,
					style: 0
				});

			      }
			  }
		  }
		  //maxVal = (Math.max.apply(Math, zvals));
       
                  // specify options
                  var options = {
                    width:  '100%',
                    height: '1000px',
                    style: 'bar',
		    backgroundColor: {fill: 'white', stroke: 'black'},
                    showPerspective: true,
                    showGrid: false,
                    showShadow: false,
                    keepAspectRatio: true,
                    verticalRatio: 0.5,
                    xValueLabel: function (x) {return "node " + streams[x].node + " thread " + streams[x].thread},
		    xLabel: "Thread ID",
		    yValueLabel: function (y) {return funcNames[y]},
		    yLabel: "Function",
	            zMin: 0,
		    zMax: maxVal,
		    zLabel: metric,
                  };
       
                  // create a graph3d
                  var container = document.getElementById('mygraph');
                  var graph3d = new vis.Graph3d(container, data, options);

	}

});
