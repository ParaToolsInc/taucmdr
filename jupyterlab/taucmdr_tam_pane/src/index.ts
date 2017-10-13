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
    JSONExt
} from '@phosphor/coreutils';

import {
    JupyterLab, JupyterLabPlugin, ILayoutRestorer
} from '@jupyterlab/application';

import {
    ICommandPalette, InstanceTracker
} from '@jupyterlab/apputils';

import {
    Message
} from '@phosphor/messaging';

import {
    Kernels
} from "./kernels";

import {
    Table
} from "./table";

import '../style/index.css';

const tam_widget_id = 'taucmdr_tam_pane';
const trial_widget_id = 'taucmdr_trial_pane';
const class_name = 'tam';

export class TAMPaneWidget extends Widget {
    app: JupyterLab;
    kernels : Kernels;

    mainContent: HTMLDivElement;

    get_table_names() : Array<string> {
        return ['projectTableDiv', 'targetTableDiv', 'applicationTableDiv', 'measurementTableDiv', 'experimentTableDiv'];
    }

    projectTableDiv : HTMLDivElement;
    targetTableDiv : HTMLDivElement;
    applicationTableDiv: HTMLDivElement;
    measurementTableDiv: HTMLDivElement;
    experimentTableDiv: HTMLDivElement;
    [propname: string] : any;

    constructor(app: JupyterLab) {
        super();

        this.kernels = new Kernels();
        this.app = app;

        this.id = tam_widget_id;
        this.title.label = 'Project';
        this.title.closable = true;
        this.addClass(tam_widget_id);

        this.mainContent = document.createElement('div');
        this.mainContent.className = 'main-content';
        this.node.appendChild(this.mainContent);

        this.get_table_names().forEach(table_name => {
            console.log(`Creating ${table_name} for table`);
            this[table_name] = document.createElement('div');
            this.mainContent.appendChild(this[table_name]);
        });
    }

    protected onAfterAttach(msg: Message): void {
        this.update();
    }

    protected onBeforeDetach(msg: Message): void {
    }

    /*
     * Clears all the tables from the view.
     */
    clear(): void {
        this.get_table_names().forEach(table_name => {
            console.log(`Clearing ${table_name}`);
            this[table_name].innerHTML = '';
        })
    }

    /*
     * Replaces the table contents of `rows` with a new table containing headings listed in `fields` and
     * values from the JSON array `rows`.
     */
    protected update_table(div: HTMLDivElement, model: string, rows: Array<Kernels.JSONResult>, fields: Array<string>): void {
        let table = new Table(rows, fields, class_name);
        div.innerHTML = "";
        div.appendChild(document.createElement('h1').appendChild(
            document.createTextNode(model)));
        div.appendChild(table.get_table());
    }

    protected update_handler(entries : Array<Kernels.JSONResult>) : void {
        entries.forEach(entry => {
            this.update_table(this[entry['model']+'TableDiv'], entry['model'], entry['rows'], entry['headers']);
        });
    }

    /*
     * Requests new data from TAU Commander and updates the table to display that data.
     */
    update(): void {
        this.clear();
        this.kernels.get_project().then(project_entries => {
            this.update_handler(project_entries);
        });
    }

    display(): void {
        this.app.shell.addToMainArea(this);
    }
}

export class ExperimentPaneWidget extends TAMPaneWidget {

    get_table_names() : Array<string> {
        return ['trialTableDiv'];
    }

    trialTableDiv : HTMLDivElement;

    constructor(app: JupyterLab) {
        console.log("Constructing the ExperimentPaneWidget!")
        super(app);
        this.id = trial_widget_id;
        this.title.label = 'Experiment';
        console.log("Done constructing the ExperimentPaneWidget!")
    }

    update(): void {
        this.clear();
        this.kernels.get_trials().then(project_entries => {
            this.update_handler(project_entries);
        });
    }

}

export let defaultTAMPane: TAMPaneWidget = null;
export let defaultExperimentPane: ExperimentPaneWidget = null;

function activate(app: JupyterLab, palette: ICommandPalette, restorer: ILayoutRestorer) {
    console.log(`JupyterLab extension ${tam_widget_id} is activated!`);

    // Add an application command to open the Project pane
    let tamPaneWidget: TAMPaneWidget;
    const open_project_command = 'tam:open_project';
    app.commands.addCommand(open_project_command, {
        label: 'Open Project Pane',
        execute: () => {
            if (!tamPaneWidget) {
                // Create a new widget if one does not exist
                tamPaneWidget = new TAMPaneWidget(app);
                if (defaultTAMPane == null) {
                    defaultTAMPane = tamPaneWidget
                }
                tamPaneWidget.update();
            }
            if (!proj_tracker.has(tamPaneWidget)) {
                // Track the state of the widget for later restoration
                proj_tracker.add(tamPaneWidget).then(r => {
                });
            }
            if (!tamPaneWidget.isAttached) {
                // Attach the widget to the main area if it's not there
                app.shell.addToMainArea(tamPaneWidget);
            } else {
                // Refresh the data in the widget
                tamPaneWidget.update();
            }
            // Activate the widget
            app.shell.activateById(tamPaneWidget.id);
        }
    });

    // Add an application command to open the Experiment pane
    let experimentPaneWidget: ExperimentPaneWidget;
    const open_experiment_command = 'tam:open_experiment';
    app.commands.addCommand(open_experiment_command, {
        label: 'Open Experiment Pane',
        execute: () => {
            console.log("Should open experiment pane");
            if (!experimentPaneWidget) {
                // Create a new widget if one does not exist
                experimentPaneWidget = new ExperimentPaneWidget(app);
                if (defaultExperimentPane == null) {
                    defaultExperimentPane = experimentPaneWidget
                }
                experimentPaneWidget.update();
            }
            if (!exp_tracker.has(experimentPaneWidget)) {
                // Track the state of the widget for later restoration
                exp_tracker.add(experimentPaneWidget).then(r => {
                });
            }
            if (!experimentPaneWidget.isAttached) {
                // Attach the widget to the main area if it's not there
                app.shell.addToMainArea(experimentPaneWidget);
            } else {
                // Refresh the data in the widget
                experimentPaneWidget.update();
            }
            // Activate the widget
            app.shell.activateById(experimentPaneWidget.id);
        }
    });

    // Add the command to the palette.
    palette.addItem({command: open_project_command, category: 'TAU Commander'});
    palette.addItem({command: open_experiment_command, category: 'TAU Commander'});

    // Track and restore the widget state
    let proj_tracker = new InstanceTracker<Widget>({namespace: tam_widget_id});
    restorer.restore(proj_tracker, {
        command: open_project_command,
        args: () => JSONExt.emptyObject,
        name: () => 'project-view'
    });
    let exp_tracker = new InstanceTracker<Widget>({namespace: trial_widget_id});
    restorer.restore(exp_tracker, {
        command: open_experiment_command,
        args: () => JSONExt.emptyObject,
        name: () => 'experiment-view'
    });
}

const extension: JupyterLabPlugin<void> = {
    id: tam_widget_id,
    autoStart: true,
    requires: [ICommandPalette, ILayoutRestorer],
    activate: activate
};

export default extension;
