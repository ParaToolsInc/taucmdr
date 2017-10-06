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

const widget_id = 'taucmdr_tam_pane';
const class_name = 'tam';

export class TAMPaneWidget extends Widget {
    app: JupyterLab;
    kernels : Kernels;

    mainContent: HTMLDivElement;

    readonly table_names = ['projectTableDiv', 'targetTableDiv', 'applicationTableDiv', 'measurementTableDiv', 'experimentTableDiv'];

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

        this.id = widget_id;
        this.title.label = 'Commander';
        this.title.closable = true;
        this.addClass(widget_id);

        this.mainContent = document.createElement('div');
        this.mainContent.className = 'main-content';
        this.node.appendChild(this.mainContent);

        this.table_names.forEach(table_name => {
            this[table_name] = document.createElement('div');
            this.mainContent.appendChild(this[table_name]);
        });
    }

    protected onAfterAttach(msg: Message): void {
        this.update();
        console.log("after attach");
    }

    protected onBeforeDetach(msg: Message): void {
    }

    update_table(div: HTMLDivElement, model: string, rows: Array<Kernels.JSONResult>, fields: Array<string>): void {
        this.kernels.get_project().then(project => {
            let table = new Table(rows, fields, class_name);
            div.innerHTML = "";
            div.appendChild(document.createElement('h1').appendChild(
                document.createTextNode(model)));
            div.appendChild(table.get_table());
        }, reason => {
            throw new Error(reason);
        });
    }

    update(): void {
        this.kernels.get_project().then(project_entries => {
            project_entries.forEach(entry => {
                console.log(`Updating a ${entry['model']}`);
                this.update_table(this[entry['model']+'TableDiv'], entry['model'], entry['rows'], entry['headers']);
            });
        });
    }

    display(): void {
        this.app.shell.addToMainArea(this);
    }


}

export let defaultTAMPane: TAMPaneWidget = null;

function activate(app: JupyterLab, palette: ICommandPalette, restorer: ILayoutRestorer) {
    console.log(`JupyterLab extension ${widget_id} is activated!`);

    // Declare a widget variable
    let widget: TAMPaneWidget;

    // Add an application command
    const command: string = 'tam:open';
    app.commands.addCommand(command, {
        label: 'Open TAM Pane',
        execute: () => {
            if (!widget) {
                // Create a new widget if one does not exist
                widget = new TAMPaneWidget(app);
                if (defaultTAMPane == null) {
                    defaultTAMPane = widget
                }
                widget.update();
            }
            if (!tracker.has(widget)) {
                // Track the state of the widget for later restoration
                tracker.add(widget).then(r => {
                });
            }
            if (!widget.isAttached) {
                // Attach the widget to the main area if it's not there
                app.shell.addToMainArea(widget);
            } else {
                // Refresh the data in the widget
                widget.update();
            }
            // Activate the widget
            app.shell.activateById(widget.id);
        }
    });

    // Add the command to the palette.
    palette.addItem({command, category: 'Tutorial'});

    // Track and restore the widget state
    let tracker = new InstanceTracker<Widget>({namespace: widget_id});
    restorer.restore(tracker, {
        command,
        args: () => JSONExt.emptyObject,
        name: () => widget_id
    });
}

const extension: JupyterLabPlugin<void> = {
    id: widget_id,
    autoStart: true,
    requires: [ICommandPalette, ILayoutRestorer],
    activate: activate
};

export default extension;
