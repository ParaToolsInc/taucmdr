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
Object.defineProperty(exports, "__esModule", { value: true });
var services_1 = require("@jupyterlab/services");
var Kernels = (function () {
    function Kernels() {
        this.start_session().then(function (r) { });
    }
    Kernels.prototype.get_project = function () {
        return this.execute_kernel(Kernels.getProjectKernel).then(function (stream) {
            return stream.split("\n").slice(0, -1).map(function (entry) {
                return JSON.parse(entry);
            });
        }, function (reason) {
            throw new Error(reason);
        });
    };
    Kernels.prototype.execute_kernel = function (kernel) {
        return this.start_session().then(function (session) {
            console.log("Executing: ", kernel);
            var future = session.kernel.requestExecute({ code: kernel });
            var stream = "";
            var error = false;
            var errString = "";
            future.onIOPub = function (msg) {
                if (msg.header.msg_type == "stream") {
                    stream = stream.concat(msg.content.text.toString());
                }
                else if (msg.header.msg_type == "error") {
                    error = true;
                    errString = msg.content.ename + "\n" + msg.content.evalue + "\n" + msg.content.traceback;
                }
            };
            return future.done.then(function (r) {
                if (error) {
                    throw new Error(errString);
                }
                console.log("Got result: ", stream);
                return stream;
            }, function (reason) {
                throw new Error(reason);
            });
        });
    };
    Kernels.prototype.start_session = function () {
        var _this = this;
        if (!this.session) {
            return services_1.Session.findByPath(Kernels.session_path).then(function (model) {
                return services_1.Session.connectTo(model.id).then(function (s) {
                    _this.session = s;
                    return _this.session;
                });
            }, function () {
                var options = {
                    kernelName: 'python',
                    path: Kernels.session_path
                };
                return services_1.Session.startNew(options).then(function (s) {
                    _this.session = s;
                    return _this.session;
                }, function (r) {
                    throw new Error("Unable to start session");
                });
            });
        }
        else {
            return Promise.resolve(this.session);
        }
    };
    ;
    return Kernels;
}());
exports.Kernels = Kernels;
(function (Kernels) {
    Kernels.session_path = 'taucmdr_tam_pane.ipynb';
    Kernels.getProjectKernel = "\ndef get_project():\n    from taucmdr.model.project import Project\n    selected = Project.selected()\n    from taucmdr.cli.commands.project.list import COMMAND as project_list_command\n    return project_list_command.main([selected['name'], '--json'])\nget_project()\n";
    var JSONResult = (function () {
        function JSONResult() {
        }
        return JSONResult;
    }());
    Kernels.JSONResult = JSONResult;
})(Kernels = exports.Kernels || (exports.Kernels = {}));
exports.Kernels = Kernels;
