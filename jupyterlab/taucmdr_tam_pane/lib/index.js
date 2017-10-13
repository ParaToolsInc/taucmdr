"use strict";
/* Copyright (c) 2017, ParaTools, Inc.
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 * (1) Redistributions of source code must retain the above copyright notice,
 *     this list of conditions and the following disclaimer.
 * (2) Redistributions in binary form must reproduce the above copyright notice,
 *     this list of conditions and the following disclaimer in the documentation
 *     and/or other materials provided with the distribution.
 * (3) Neither the name of ParaTools, Inc. nor the names of its contributors may
 *     be used to endorse or promote products derived from this software without
 *     specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */
var __extends = (this && this.__extends) || (function () {
    var extendStatics = Object.setPrototypeOf ||
        ({ __proto__: [] } instanceof Array && function (d, b) { d.__proto__ = b; }) ||
        function (d, b) { for (var p in b) if (b.hasOwnProperty(p)) d[p] = b[p]; };
    return function (d, b) {
        extendStatics(d, b);
        function __() { this.constructor = d; }
        d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
var widgets_1 = require("@phosphor/widgets");
var coreutils_1 = require("@phosphor/coreutils");
var application_1 = require("@jupyterlab/application");
var apputils_1 = require("@jupyterlab/apputils");
var kernels_1 = require("./kernels");
var table_1 = require("./table");
require("../style/index.css");
var tam_widget_id = 'taucmdr_tam_pane';
var trial_widget_id = 'taucmdr_trial_pane';
var class_name = 'tam';
var TAMPaneWidget = (function (_super) {
    __extends(TAMPaneWidget, _super);
    function TAMPaneWidget(app) {
        var _this = _super.call(this) || this;
        _this.kernels = new kernels_1.Kernels();
        _this.app = app;
        _this.id = tam_widget_id;
        _this.title.label = 'Project';
        _this.title.closable = true;
        _this.addClass(tam_widget_id);
        _this.mainContent = document.createElement('div');
        _this.mainContent.className = 'main-content';
        _this.node.appendChild(_this.mainContent);
        _this.get_table_names().forEach(function (table_name) {
            console.log("Creating " + table_name + " for table");
            _this[table_name] = document.createElement('div');
            _this.mainContent.appendChild(_this[table_name]);
        });
        return _this;
    }
    TAMPaneWidget.prototype.get_table_names = function () {
        return ['projectTableDiv', 'targetTableDiv', 'applicationTableDiv', 'measurementTableDiv', 'experimentTableDiv'];
    };
    TAMPaneWidget.prototype.onAfterAttach = function (msg) {
        this.update();
    };
    TAMPaneWidget.prototype.onBeforeDetach = function (msg) {
    };
    /*
     * Clears all the tables from the view.
     */
    TAMPaneWidget.prototype.clear = function () {
        var _this = this;
        this.get_table_names().forEach(function (table_name) {
            console.log("Clearing " + table_name);
            _this[table_name].innerHTML = '';
        });
    };
    /*
     * Replaces the table contents of `rows` with a new table containing headings listed in `fields` and
     * values from the JSON array `rows`.
     */
    TAMPaneWidget.prototype.update_table = function (div, model, rows, fields) {
        var table = new table_1.Table(rows, fields, class_name);
        div.innerHTML = "";
        div.appendChild(document.createElement('h1').appendChild(document.createTextNode(model)));
        div.appendChild(table.get_table());
    };
    TAMPaneWidget.prototype.update_handler = function (entries) {
        var _this = this;
        entries.forEach(function (entry) {
            _this.update_table(_this[entry['model'] + 'TableDiv'], entry['model'], entry['rows'], entry['headers']);
        });
    };
    /*
     * Requests new data from TAU Commander and updates the table to display that data.
     */
    TAMPaneWidget.prototype.update = function () {
        var _this = this;
        this.clear();
        this.kernels.get_project().then(function (project_entries) {
            _this.update_handler(project_entries);
        });
    };
    TAMPaneWidget.prototype.display = function () {
        this.app.shell.addToMainArea(this);
    };
    return TAMPaneWidget;
}(widgets_1.Widget));
exports.TAMPaneWidget = TAMPaneWidget;
var ExperimentPaneWidget = (function (_super) {
    __extends(ExperimentPaneWidget, _super);
    function ExperimentPaneWidget(app) {
        var _this = this;
        console.log("Constructing the ExperimentPaneWidget!");
        _this = _super.call(this, app) || this;
        _this.id = trial_widget_id;
        _this.title.label = 'Experiment';
        console.log("Done constructing the ExperimentPaneWidget!");
        return _this;
    }
    ExperimentPaneWidget.prototype.get_table_names = function () {
        return ['trialTableDiv'];
    };
    ExperimentPaneWidget.prototype.update = function () {
        var _this = this;
        this.clear();
        this.kernels.get_trials().then(function (project_entries) {
            _this.update_handler(project_entries);
        });
    };
    return ExperimentPaneWidget;
}(TAMPaneWidget));
exports.ExperimentPaneWidget = ExperimentPaneWidget;
exports.defaultTAMPane = null;
exports.defaultExperimentPane = null;
function activate(app, palette, restorer) {
    console.log("JupyterLab extension " + tam_widget_id + " is activated!");
    // Add an application command to open the Project pane
    var tamPaneWidget;
    var open_project_command = 'tam:open_project';
    app.commands.addCommand(open_project_command, {
        label: 'Open Project Pane',
        execute: function () {
            if (!tamPaneWidget) {
                // Create a new widget if one does not exist
                tamPaneWidget = new TAMPaneWidget(app);
                if (exports.defaultTAMPane == null) {
                    exports.defaultTAMPane = tamPaneWidget;
                }
                tamPaneWidget.update();
            }
            if (!proj_tracker.has(tamPaneWidget)) {
                // Track the state of the widget for later restoration
                proj_tracker.add(tamPaneWidget).then(function (r) {
                });
            }
            if (!tamPaneWidget.isAttached) {
                // Attach the widget to the main area if it's not there
                app.shell.addToMainArea(tamPaneWidget);
            }
            else {
                // Refresh the data in the widget
                tamPaneWidget.update();
            }
            // Activate the widget
            app.shell.activateById(tamPaneWidget.id);
        }
    });
    // Add an application command to open the Experiment pane
    var experimentPaneWidget;
    var open_experiment_command = 'tam:open_experiment';
    app.commands.addCommand(open_experiment_command, {
        label: 'Open Experiment Pane',
        execute: function () {
            console.log("Should open experiment pane");
            if (!experimentPaneWidget) {
                // Create a new widget if one does not exist
                experimentPaneWidget = new ExperimentPaneWidget(app);
                if (exports.defaultExperimentPane == null) {
                    exports.defaultExperimentPane = experimentPaneWidget;
                }
                experimentPaneWidget.update();
            }
            if (!exp_tracker.has(experimentPaneWidget)) {
                // Track the state of the widget for later restoration
                exp_tracker.add(experimentPaneWidget).then(function (r) {
                });
            }
            if (!experimentPaneWidget.isAttached) {
                // Attach the widget to the main area if it's not there
                app.shell.addToMainArea(experimentPaneWidget);
            }
            else {
                // Refresh the data in the widget
                experimentPaneWidget.update();
            }
            // Activate the widget
            app.shell.activateById(experimentPaneWidget.id);
        }
    });
    // Add the command to the palette.
    palette.addItem({ command: open_project_command, category: 'TAU Commander' });
    palette.addItem({ command: open_experiment_command, category: 'TAU Commander' });
    // Track and restore the widget state
    var proj_tracker = new apputils_1.InstanceTracker({ namespace: tam_widget_id });
    restorer.restore(proj_tracker, {
        command: open_project_command,
        args: function () { return coreutils_1.JSONExt.emptyObject; },
        name: function () { return 'project-view'; }
    });
    var exp_tracker = new apputils_1.InstanceTracker({ namespace: trial_widget_id });
    restorer.restore(exp_tracker, {
        command: open_experiment_command,
        args: function () { return coreutils_1.JSONExt.emptyObject; },
        name: function () { return 'experiment-view'; }
    });
}
var extension = {
    id: tam_widget_id,
    autoStart: true,
    requires: [apputils_1.ICommandPalette, application_1.ILayoutRestorer],
    activate: activate
};
exports.default = extension;
