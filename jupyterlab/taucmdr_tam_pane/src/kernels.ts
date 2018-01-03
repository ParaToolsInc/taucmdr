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

import {
    Kernel
} from '@jupyterlab/services';


/*
 * The Kernels class and namespace are in charge of managing communication between
 * the TAU Commander GUI and the Python backend.
 */
export class Kernels {

    session: Session.ISession;

    constructor() {
        this.start_session().then(r=>{});
    }

    /*
     * Get all the project, targets, applications, measurements, and experiments
     * for the currently selected TAU Commander project. These are returned as a list
     * of JSON objects having the form:
     *
     *  {
     *      model: model name (string),
     *      headers: the names of the column headers for the model (array of string),
     *      rows: the data for each row, in the same order as listed in headers (array of array)
     *  }
     */
    get_project() : Promise<Array<Kernels.JSONResult>> {
        return this.handle_listing_command(Kernels.getProjectKernel);
    }

    /*
     * Get all the trials for the currently selected experiment.
     * These are returned as a list of JSON objects having the form:
     *
     *  {
     *      model: model name (string),
     *      headers: the names of the column headers for the model (array of string),
     *      rows: the data for each row, in the same order as listed in headers (array of array)
     *  }
     */
    get_trials() : Promise<Array<Kernels.JSONResult>> {
        return this.handle_listing_command(Kernels.getTrialsKernel);
    }

    /*
     * Get a list of the available analyses. These are returned as a JSON object having the form:
     *
     *  [
     *      {
     *          name: analysis name, to be used when invoking the analysis (string),
     *          desc: description of the analysis, to be presented to the user (string)
     *      }, ...
     *  ]
     */
    get_analyses() : Promise<Kernels.JSONResult> {
        return this.handle_single_command(Kernels.getAnalysesKernel);
    }

    /*
     * Get a list of the available analyses. These are returned as a JSON object having the form:
     *
     *  {
     *      model: model name (string),
     *      headers: the names of the column headers for the model (array of string),
     *      rows: the data for each row, in the same order as listed in headers (array of array)
     *  }
     */

    get_analyses_as_table() : Promise<Array<Kernels.JSONResult>> {
        return this.handle_listing_command(Kernels.getAnalysesAsTableKernel);
    }

    /*
     * Run an analysis on the analysis identified by `analysis_name` on the TAU Commander
     * objects having hashes listed in `hashes`. Returns a JSON object indicating the path to
     * the created notebook having the form:
     *
     *  {
     *      path: path to created notebook (string)
     *  }
     */
    run_analysis(analysis_name : string, hashes : Array<string>) : Promise<Kernels.JSONResult> {
        let kernelCode = `
${Kernels.runAnalysisKernel}
print(run_analysis('${analysis_name}', ${JSON.stringify(hashes)})) 
`;
        return this.handle_single_command(kernelCode);
    }

    /*
     * Run an analysis on the analysis identified by `analysis_name` on the TAU Commander
     * objects having hashes listed in `hashes`. Returns a JSON object indicating the path to
     * the created notebook having the form:
     *
     *  {
     *      path: path to created notebook (string)
     *  }
     */
    run_analysis_with_args(analysis_name : string, hashes : Array<string>, args: string) : Promise<Kernels.JSONResult> {
        if(args == null || args == "") {
            return this.run_analysis(analysis_name, hashes);
        } else {
            let kernelCode = `
${this.runAnalysisKernelWithArgs(args)}
print(run_analysis('${analysis_name}', ${JSON.stringify(hashes)})) 
    `;
            return this.handle_single_command(kernelCode);
        }
    }

    /*
     * Get the cells which when executed carry out an analysis as identified by `analysis_name`
     * on the TAU Commander objects having hashes listed in `hashes`.
     * Returns a JSON object indicating the path to the created notebook having the form:
     *
     *  [
     *       {
     *           source: string,
     *           cell_type: string,
     *           metadata: object,
     *           execution_count: number,
     *           output_cells: [object]
     *       }
     *  ]
     */
    get_analysis_cells(analysis_name : string, hashes : Array<string>) : Promise<Kernels.JSONResult> {
        let kernelCode = `
${Kernels.getAnalysisCellsKernel}
print(run_analysis('${analysis_name}', ${JSON.stringify(hashes)})) 
`;
        return this.handle_single_command(kernelCode);
    }

    get_cwd() : Promise<string> {
        return this.handle_single_command(Kernels.getCwdKernel).then(result => {
            return result.cwd;
        });
    }

    get_kernel_model() : Promise<Kernel.IModel> {
        return this.start_session().then(s => {
            return {id: s.kernel.id, name: s.kernel.name};
        });
    }

    protected handle_listing_command(command: string) : Promise<Array<Kernels.JSONResult>> {
        return this.execute_kernel(command).then(stream => {
            return stream.split("\n").slice(0, -1).map(entry => {
                return JSON.parse(entry);
            });
        }, reason => {
            throw new Error(reason);
        });
    }

    protected handle_single_command(command: string): Promise<Kernels.JSONResult> {
        return this.execute_kernel(command).then(stream => {
            return JSON.parse(stream);
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
                    type: 'python2',
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

    protected runAnalysisKernelWithArgs(args : string) : string {
        return Kernels.runAnalysisBase + `
    return json.dumps({"path": analysis.create_notebook(trials, '.', ${args})})
`
    }

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

    export const getTrialsKernel = `
def get_trials():
    from taucmdr.cli.commands.trial.list import COMMAND as trial_list_command
    return trial_list_command.main(['--json'])
get_trials()    
`;

    export const getAnalysesKernel = `
def get_analyses():
    import json
    import taucmdr.analysis as analysis
    return json.dumps([{'name': a.name, 'desc': a.description} for a in analysis.get_analyses().values()])
print(get_analyses())
`;

    export const getAnalysesAsTableKernel = `
def get_analyses_as_table():
    import json
    import taucmdr.analysis as analysis    
    return json.dumps({'model': 'analysis', 'headers': ['Name', 'Description'], 'rows': [{'Name': a.name, 'Description': a.description} for a in analysis.get_analyses().values()]}) 

print(get_analyses_as_table())
`;

    export const runAnalysisBase = `
def run_analysis(name, hashes):
    import json
    from taucmdr.analysis import get_analysis
    from taucmdr.model.trial import Trial
    from taucmdr.cf.storage.levels import PROJECT_STORAGE
    trials = [Trial.controller(PROJECT_STORAGE).search_hash(h)[0] for h in hashes]
    analysis = get_analysis(name)
`;

    export const runAnalysisKernel = runAnalysisBase + `
    return json.dumps({"path": analysis.create_notebook(trials, '.')})
`;

    export const getAnalysisCellsKernel = runAnalysisBase + `
    return json.dumps({"cells": analysis.get_cells(trials, '.')})
`;

    export const getCwdKernel = `
def get_cwd():
    import os
    import json
    return json.dumps({'cwd': os.getcwd()})
print(get_cwd())
`;


    export class JSONResult {
        readonly [propname: string]: any;
    }

}

