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
exports.__esModule = true;
var widgets_1 = require("@phosphor/widgets");
var coreutils_1 = require("@phosphor/coreutils");
var application_1 = require("@jupyterlab/application");
var apputils_1 = require("@jupyterlab/apputils");
var kernels_1 = require("./kernels");
require("../style/index.css");
var widget_id = 'taucmdr_tam_pane';
var TAMPaneWidget = (function (_super) {
    __extends(TAMPaneWidget, _super);
    function TAMPaneWidget(app) {
        var _this = _super.call(this) || this;
        _this.app = app;
        _this.id = widget_id;
        _this.title.label = 'Commander';
        _this.title.closable = true;
        _this.addClass(widget_id);
        _this.mainContent = document.createElement('div');
        _this.mainContent.className = 'main-content';
        _this.node.appendChild(_this.mainContent);
        _this.mainContent.appendChild(document.createTextNode(kernels_1.Kernels.getProjectKernel));
        return _this;
    }
    TAMPaneWidget.prototype.onAfterAttach = function (msg) {
        console.log("after attach");
    };
    TAMPaneWidget.prototype.onBeforeDetach = function (msg) {
        console.log("before detach");
    };
    TAMPaneWidget.prototype.update = function () {
    };
    TAMPaneWidget.prototype.display = function () {
        this.app.shell.addToMainArea(this);
    };
    return TAMPaneWidget;
}(widgets_1.Widget));
exports.TAMPaneWidget = TAMPaneWidget;
exports.defaultTAMPane = null;
function activate(app, palette, restorer) {
    console.log("JupyterLab extension " + widget_id + " is activated!");
    // Declare a widget variable
    var widget;
    // Add an application command
    var command = 'tam:open';
    app.commands.addCommand(command, {
        label: 'Open TAM Pane',
        execute: function () {
            if (!widget) {
                // Create a new widget if one does not exist
                widget = new TAMPaneWidget(app);
                if (exports.defaultTAMPane == null) {
                    exports.defaultTAMPane = widget;
                }
                widget.update();
            }
            if (!tracker.has(widget)) {
                // Track the state of the widget for later restoration
                tracker.add(widget);
            }
            if (!widget.isAttached) {
                // Attach the widget to the main area if it's not there
                app.shell.addToMainArea(widget);
            }
            else {
                // Refresh the comic in the widget
                widget.update();
            }
            // Activate the widget
            app.shell.activateById(widget.id);
        }
    });
    // Add the command to the palette.
    palette.addItem({ command: command, category: 'Tutorial' });
    // Track and restore the widget state
    var tracker = new apputils_1.InstanceTracker({ namespace: widget_id });
    restorer.restore(tracker, {
        command: command,
        args: function () { return coreutils_1.JSONExt.emptyObject; },
        name: function () { return widget_id; }
    });
}
var extension = {
    id: widget_id,
    autoStart: true,
    requires: [apputils_1.ICommandPalette, application_1.ILayoutRestorer],
    activate: activate
};
exports["default"] = extension;
