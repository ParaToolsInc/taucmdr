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
    JupyterLab
} from "@jupyterlab/application";

import {
    TauCmdrPaneWidget
} from "./tam_widget";

import {
    Kernels
} from "./kernels";


export const experiment_widget_id = 'taucmdr_trial_pane';

export class ExperimentPaneWidget extends TauCmdrPaneWidget {

    get_table_names() : Array<string> {
        return ['trialTableDiv'];
    }

    trialTableDiv : HTMLDivElement;

    constructor(app: JupyterLab) {
        super(app, experiment_widget_id, 'Experiment');
    }

    run_analysis(analysis_name : string) : void {
        let selected_trials = this.table.get_selected();
        console.log(`Should run ${analysis_name} on ${selected_trials}`);
        this.kernels.run_analysis(analysis_name, selected_trials).then(response => {
            console.log(response.path);
        });
    }

    update_analyses(): void {
        this.kernels.get_analyses().then(analyses => {
            let span = document.createElement('span');
            let select = document.createElement('select');
            (analyses as Array<Kernels.JSONResult>).forEach(analysis => {

                let option = document.createElement('option');
                option.value = analysis.name;
                option.appendChild(document.createTextNode(analysis.desc));
                select.appendChild(option);
            });
            span.appendChild(select);
            let runButton = document.createElement('button');
            runButton.appendChild(document.createTextNode('Run'));
            runButton.addEventListener('click', () => {
                this.run_analysis(select.options[select.selectedIndex].value);
            });
            span.appendChild(runButton);
            this.table.add_as_footer_row(span);
        }, reason => {
            throw new Error(reason);
        });
    }

    clear(): void {
        super.clear();
    }

    update(): void {
        this.clear();
        this.kernels.get_trials().then(project_entries => {
            this.update_handler(project_entries, true, 'Hash');
            this.update_analyses();
        });
    }

}
