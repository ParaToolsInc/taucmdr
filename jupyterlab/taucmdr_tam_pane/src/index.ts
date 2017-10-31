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
    ProjectPaneWidget, project_widget_id
} from "./project";

import {
    ExperimentPaneWidget, experiment_widget_id
} from "./experiment";

import {
    AnalysisSidebarWidget, analysis_widget_id
} from "./analysis";

import '../style/index.css';

declare global {
    export interface Window {
        defaultProjectPane: ProjectPaneWidget;
        defaultExperimentPane: ExperimentPaneWidget;
        defaultAnalysisSidebar: AnalysisSidebarWidget;
    }
}

// To prevent the compiler from complaining that Window is unused, even though it isn't.
export let foo : Window;

export let defaultTAMPane: ProjectPaneWidget = null;

export let defaultExperimentPane: ExperimentPaneWidget = null;

function activate(app: JupyterLab, palette: ICommandPalette, restorer: ILayoutRestorer) {
    console.log(`JupyterLab extension ${project_widget_id} is activated!`);

    // Add an application command to open the Project pane
    let projectPaneWidget: ProjectPaneWidget;
    const open_project_command = 'tam:open_project';
    app.commands.addCommand(open_project_command, {
        label: 'Open Project Pane',
        execute: () => {
            if (!projectPaneWidget) {
                // Create a new widget if one does not exist
                projectPaneWidget = new ProjectPaneWidget(app);
                if (defaultTAMPane == null) {
                    defaultTAMPane = projectPaneWidget;
                    window.defaultProjectPane = defaultTAMPane;
                }
            }
            if (!proj_tracker.has(projectPaneWidget)) {
                // Track the state of the widget for later restoration
                proj_tracker.add(projectPaneWidget).then(r => {
                });
            }
            if (!projectPaneWidget.isAttached) {
                // Attach the widget to the main area if it's not there
                app.shell.addToMainArea(projectPaneWidget);
            } else {
                // Refresh the data in the widget
                projectPaneWidget.update();
            }
            // Activate the widget
            app.shell.activateById(projectPaneWidget.id);
        }
    });

    // Add an application command to open the Experiment pane
    let experimentPaneWidget: ExperimentPaneWidget;
    const open_experiment_command = 'tam:open_experiment';
    app.commands.addCommand(open_experiment_command, {
        label: 'Open Experiment Pane',
        execute: () => {
            if (!experimentPaneWidget) {
                // Create a new widget if one does not exist
                experimentPaneWidget = new ExperimentPaneWidget(app);
                if (defaultExperimentPane == null) {
                    defaultExperimentPane = experimentPaneWidget;
                    window.defaultExperimentPane = defaultExperimentPane;
                }
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
    let proj_tracker = new InstanceTracker<Widget>({namespace: project_widget_id});
    restorer.restore(proj_tracker, {
        command: open_project_command,
        args: () => JSONExt.emptyObject,
        name: () => 'project-view'
    });
    let exp_tracker = new InstanceTracker<Widget>({namespace: experiment_widget_id});
    restorer.restore(exp_tracker, {
        command: open_experiment_command,
        args: () => JSONExt.emptyObject,
        name: () => 'experiment-view'
    });

    // Add a sidebar to select and run analyses
    let analysisSidebarWidget : AnalysisSidebarWidget;
    analysisSidebarWidget = new AnalysisSidebarWidget(app);
    window.defaultAnalysisSidebar = analysisSidebarWidget;
    app.shell.addToLeftArea(analysisSidebarWidget, {rank: 2000});
    restorer.add(analysisSidebarWidget, analysis_widget_id);
}

const extension: JupyterLabPlugin<void> = {
    id: project_widget_id,
    autoStart: true,
    requires: [ICommandPalette, ILayoutRestorer],
    activate: activate
};

export default extension;
