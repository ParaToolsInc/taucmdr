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
    Widget
} from '@phosphor/widgets';

import {
    JupyterLab, JupyterLabPlugin, ILayoutRestorer
} from '@jupyterlab/application';

import {
    ICommandPalette, Dialog, showDialog
} from '@jupyterlab/apputils';

import {
    Session
} from '@jupyterlab/services';

import {
    Message
} from '@phosphor/messaging';

import '../style/index.css';

const widget_id = 'taucmdr_experiment_selector';

interface IExperimentsResult {
    readonly Hash: string;
    readonly Name: string;
    readonly Trials: string;
    readonly Selected: boolean;
    readonly [propName: string]: any;
}

function showErrorMessage(title: string, error: any): Promise<void> {
    console.error(error);
    let options = {
        title: title,
        body: error.message || String(error).replace(
            /[\u001b\u009b][[()#;?]*(?:[0-9]{1,4}(?:;[0-9]{0,4})*)?[0-9A-ORZcf-nqry=><]/g, ''),
        buttons: [Dialog.okButton()],
        okText: 'DISMISS'
    };
    return showDialog(options).then(() => { /* no-op */ });
}

class ExperimentSelectorWidget extends Widget {

    readonly session_path: string = 'taucmdr_experiment_selector.ipynb';

    readonly get_experiments_kernel: string = `
import json
from taucmdr.model.experiment import Experiment
from taucmdr.model.project import Project
experiments = Experiment.controller().all()
selected_eid = Project.selected().get('experiment', None)
entries = []
for exp in experiments:
    entry = {}
    entry['Hash'] = exp.hash_digest()[-10:]
    entry['Name'] = exp['name']
    entry['Trials'] = len(exp['trials'])
    entry['Selected'] = selected_eid == exp.eid
    entries.append(entry)
print(json.dumps(entries))
`;

    readonly fields = ['Hash', 'Name', 'Trials'];

    app: JupyterLab;

    contentDiv: HTMLDivElement;
    table: HTMLTableElement;
    tHead: HTMLTableSectionElement;
    tBody: HTMLTableSectionElement;
    tHeadRow: HTMLTableRowElement;
    session: Session.ISession;

    constructor(app: JupyterLab) {
        super();
        this.app = app;
        this.id = widget_id;
        this.title.label = 'Experiments';
        this.title.closable = true;
        this.addClass(widget_id);

        this.contentDiv = document.createElement("div");
        let button = document.createElement('button');
        button.appendChild(document.createTextNode("Refresh experiment list"));
        button.addEventListener('click', () => {this.list_experiments()});
        this.contentDiv.appendChild(button);
        this.node.appendChild(this.contentDiv);
        this.table = document.createElement('table');
        this.table.className = 'table';
        this.build_header();
        this.tBody = this.table.createTBody();
        this.contentDiv.appendChild(this.table)
    };

    build_header(): void {
        this.tHead = this.table.createTHead();
        this.tHeadRow = this.tHead.insertRow();
        let firstCol = document.createElement('th');
        firstCol.className = 'empty';
        this.tHeadRow.appendChild(firstCol);
        this.fields.forEach( field => {
            let headerCol = document.createElement('th');
            headerCol.appendChild(document.createTextNode(field));
            this.tHeadRow.appendChild(headerCol);
        });
    }

    start_session(): Promise<Session.ISession> {
        if(!this.session) {
            return Session.findByPath(this.session_path).then(model => {
                return Session.connectTo(model.id).then(s => {
                    this.session = s;
                    return this.session;
                });
            }, () => {
                let options: Session.IOptions = {
                    type: 'python2',
                    path: this.session_path
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

    select_experiment(name : string) : void {
        // Ignore ConfigurationError because they are not relevant to data analysis --
        // e.g., if we are selecting the experiment to run analyses on the trials it contains,
        // we don't care that its compilers aren't available on this system.
        let kernel_code = `
def select_experiment(name):
    from taucmdr.model.experiment import Experiment
    from taucmdr.error import ConfigurationError
    try:
        Experiment.select(name)
    except ConfigurationError:
        pass
select_experiment("${name}")
`;
        this.start_session().then(s => {
            let future = this.session.kernel.requestExecute({code: kernel_code});
            future.onIOPub = msg => {
                if (msg.header.msg_type == "stream") {
                } else if(msg.header.msg_type == "error") {
                    showErrorMessage('Unable to select experiment', msg.content.ename + "\n" + msg.content.evalue);
                } else if(msg.header.msg_type == "status" && msg.content.execution_state == "idle") {
                    this.list_experiments();
                    this.app.commands.execute("tam:open_experiment").then(r=>{});
                }
            };
        }, r => {
            console.error("Unable to select experiment: " + r.toString());
            throw new Error(r);
        });
    }

    list_experiments(show_errors: boolean = true): void {
        let result : string = "";
        this.tBody.innerHTML = "";
        this.start_session().then(s => {
            let future = this.session.kernel.requestExecute({code: this.get_experiments_kernel});
            future.onIOPub = msg => {
                if (msg.header.msg_type == "stream") {
                    result = result.concat(msg.content.text.toString());
                } else if(msg.header.msg_type == "error") {
                    let errMsg : string;
                    if(msg.content.ename == "ProjectSelectionError") {
                        errMsg = "There is no project selected";
                    } else {
                        errMsg = msg.content.ename.toString() + "\n" + msg.content.evalue.toString();
                        console.log(msg.content);
                    }
                    if(show_errors) {
                        showErrorMessage("Unable to list experiments", errMsg).then(r=>{});
                    }
                } else if(msg.header.msg_type == "status" && msg.content.execution_state == "idle") {
                    let experiments: Array<IExperimentsResult> = JSON.parse(result);
                    experiments.forEach(experiment => {
                        let row = this.tBody.insertRow();
                        let button = document.createElement('button');
                        button.className = 'select';
                        button.id = experiment.Name;
                        button.addEventListener('click', event => {
                            this.select_experiment((<HTMLElement>(event.target)).id);
                        });
                        button.appendChild(document.createTextNode('Select'));
                        if(experiment.Selected) {
                            row.className = 'selected';
                        }
                        let firstCell = row.insertCell();
                        firstCell.className = 'edit-buttons';
                        firstCell.appendChild(button);
                        this.fields.forEach(field => {
                            let cell = row.insertCell();
                            cell.appendChild(document.createTextNode(experiment[field]));
                        });
                    });
                }
            };
        }, r => {
            console.error("Unable to get experiment list: " + r.toString())
            throw new Error(r);
        });
    };

    protected onAfterAttach(msg: Message): void {
        this.list_experiments(false);
    }

    protected onBeforeDetach(msg: Message): void {
    }
}

function activate(app: JupyterLab, palette: ICommandPalette, restorer: ILayoutRestorer) {
    // Declare a widget variable
    let widget: ExperimentSelectorWidget;

    widget = new ExperimentSelectorWidget(app);

    app.shell.addToLeftArea(widget, {rank: 1000});

    restorer.add(widget, widget_id);
}

const extension: JupyterLabPlugin<void> = {
    id: widget_id,
    autoStart: true,
    requires: [ICommandPalette, ILayoutRestorer],
    activate: activate
};

export default extension;