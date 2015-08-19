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
            var threads = [];
            var thread = 0;
            for(var i = 0; i<json.data.length;i++)
            {
                var jsontmp = JSON.parse(json.data[i]);
                threads.push("node: " + jsontmp[0]["node"] + " , thread: " + jsontmp[0]["thread"]);
            }
            var selectUI_tid = d3.select("#droplist_tid")
                     .append("select")
                     .attr("id", "thread")
                     .selectAll("option")
                     .data(d3.values(threads))
                     .enter().append("option")
                     .attr("value", function(d) { return d;})
                     .text(function(d) { return d;});
            var checkOption_tid = function (e) {
                    if(e === threads){
                        return d3.select(this).attr("selected", "selected");
                    }
            };
            selectUI_tid.selectAll("option").each(checkOption_tid);

            var profJson = JSON.parse(json.data[0]);
            makeTable(profJson);

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

            // Updated thread
            d3.select('select').on("change", function() {
	       thread = this.selectedIndex;
               profJson = JSON.parse(json.data[thread]);
	       makeTable(profJson);
	       pie.destroy();
	       pie = makePieChart(profJson, metric);
	       makeBarChart(profJson, metric);
            });

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


            var pie = makePieChart(profJson, metric);
            // Updated metric
	    makeBarChart(profJson, metric);
            d3.selectAll('select')
	       .filter(function(d,i){return i==1;}).on("change", function() {
               var key = this.value;
               metric = key;
               pie.destroy();
               pie = makePieChart(profJson, metric);
	       makeBarChart(profJson, metric);
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

    /**
     * Create table with profile data
     */
    function makeTable(prof) {
        // Create title for table
	$('thead').empty();
	$('tbody').empty();
        var numkeys = Object.keys(prof[1]).length;
        var caption = d3.select("thead").append("tr").append("th").attr("colspan", numkeys);
        var cap = "Node " + prof[0]['node'] + " Thread " + prof[0]['thread'];
        caption.html(cap);

        var thead = d3.select("thead").selectAll("thead")
       .data(d3.keys(prof[1]))
       .enter().append("th").text(function(d){return d});

       // Fill table
       // Create rows
       var tr = d3.select("tbody").selectAll("tr")
       .data(prof.slice(1)).enter().append("tr");

       // Cells
       var td = tr.selectAll("td")
         .data(function(d){return d3.values(d)})
         .enter().append("td")
         .text(function(d) {return d});
    }

    function makePieChart(prof, metric) {
         var pie;

         if(isNaN(Number(prof[1][metric])))
         {
             alert("Not a valid metric!");
             pie = new d3pie("pieChart", {});
         }
         else{ 
         var cont=[];
         for(var i=0; i< prof.length; i++){
             cont.push({"label": prof[i]['Function Name'], "value": Number(prof[i][metric])});
         }
        pie = new d3pie("pieChart", {
	"header": {
		"title": {
			"text": "Profile",
			"fontSize": 24,
			"font": "open sans"
		},
		"subtitle": {
			"text": "node " + prof[0]["node"] + ", thread: " + prof[0]["thread"],
			"fontSize": 12,
			"font": "open sans"
		},
		"titleSubtitlePadding": 9
	},
	"footer": {
		"fontSize": 10,
		"font": "open sans",
		"location": "bottom-left"
	},
	"size": {
		"canvasWidth": 800,
		"pieOuterRadius": "90%"
	},
	"data": {
		"sortOrder": "value-desc",
		"content": cont
	},
	"labels": {
		"outer": {
			"pieDistance": 32
		},
		"inner": {
			"hideWhenLessThanPercentage": 3
		},
		"mainLabel": {
			"fontSize": 11
		},
		"percentage": {
			"color": "#ffffff",
			"decimalPlaces": 0
		},
		"value": {
			"color": "#adadad",
			"fontSize": 11
		},
		"lines": {
			"enabled": true
		},
		"truncation": {
			"enabled": true
		}
	},
	"effects": {
		"pullOutSegmentOnClick": {
			"effect": "linear",
			"speed": 400,
			"size": 8
		}
	},
	"misc": {
		"gradient": {
			"enabled": true,
			"percentage": 100
		}
	}
});
    }
        return pie;
}
    function makeBarChart(prof, metric) {
         var fnames=['Function Names'];
         var cont=[metric];
         for(var i=1; i< prof.length; i++){
             fnames.push(prof[i]['Function Name']);
	     cont.push(Number(prof[i][metric]));
         }
	var chart = c3.generate({
	    bindto: '#bar-chart',
	    data: {
	      x: 'Function Names',
	      columns: [
		fnames,
		cont
	      ],
	      groups: [
		      ['Exclusive Time']
		      ],
	      type: 'bar'
	    },
	    bar: {
		    width: {
			    ratio: 0.5
		    }
	    },
	    padding: {left: 400},
	    axis: {
		    x : {
			    type: 'category',
			    label: {
				    text: 'Function Name',
				    position: 'outer-middle'
			    },
			    tick: {
				    multiline: false,
				    centered: true
			    }
		    },
		    y: {
			    label:{
				    text: cont[0],
				    position: 'outer-middle'
			    }
		    },
		    rotated: true
	    },
	    legend: {
		    show: false
	    }
	});
    }
});
