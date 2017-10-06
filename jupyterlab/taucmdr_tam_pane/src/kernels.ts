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

import {
    Session
} from '@jupyterlab/services';

export class Kernels {

    session: Session.ISession;

    constructor() {
        this.start_session().then(r=>{});
    }

    get_project() : Promise<Array<Kernels.JSONResult>> {
        return this.execute_kernel(Kernels.getProjectKernel).then(stream => {
            return stream.split("\n").slice(0, -1).map(entry => {
               return JSON.parse(entry);
            });
        }, reason => {
            throw new Error(reason);
        });
    }

    protected execute_kernel(kernel: string) : Promise<string> {
        return this.start_session().then(session => {
            console.log("Executing: ", kernel);
            let future = session.kernel.requestExecute({code: kernel});
            let stream : string = "";
            let error : boolean = false;
            let errString : string = "";
            future.onIOPub = msg => {
                if (msg.header.msg_type == "stream") {
                    stream = stream.concat(msg.content.text.toString());
                } else if (msg.header.msg_type == "error") {
                    error = true;
                    errString = msg.content.ename + "\n" + msg.content.evalue + "\n" + msg.content.traceback;
                }
            };
            return future.done.then(r => {
                if(error) {
                    throw new Error(errString);
                }
                console.log("Got result: ", stream);
                return stream;
            }, reason => {
                throw new Error(reason);
            });
        });
    }

    protected start_session(): Promise<Session.ISession> {
        if (!this.session) {
            return Session.findByPath(Kernels.session_path).then(model => {
                return Session.connectTo(model.id).then(s => {
                    this.session = s;
                    return this.session;
                });
            }, () => {
                let options: Session.IOptions = {
                    kernelName: 'python',
                    path: Kernels.session_path
                };
                return Session.startNew(options).then(s => {
                    this.session = s;
                    return this.session;
                }, r => {
                    throw new Error("Unable to start session")
                });
            })
        } else {
            return Promise.resolve(this.session);
        }
    };
}

export namespace Kernels {

    export const session_path = 'taucmdr_tam_pane.ipynb';

    export const getProjectKernel = `
def get_project():
    from taucmdr.model.project import Project
    selected = Project.selected()
    from taucmdr.cli.commands.project.list import COMMAND as project_list_command
    return project_list_command.main([selected['name'], '--json'])
get_project()
`;

    export class JSONResult {
        readonly [propname: string]: any;
    }

}

