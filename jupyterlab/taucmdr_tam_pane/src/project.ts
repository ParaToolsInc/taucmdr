import {
    JupyterLab
} from '@jupyterlab/application';

import {
    TauCmdrPaneWidget
} from "./tam_widget";


export const project_widget_id = 'taucmdr_tam_pane';

export class ProjectPaneWidget extends TauCmdrPaneWidget {

    get_table_names() : Array<string> {
        return ['projectTableDiv', 'targetTableDiv', 'applicationTableDiv', 'measurementTableDiv', 'experimentTableDiv'];
    }

    projectTableDiv : HTMLDivElement;
    targetTableDiv : HTMLDivElement;
    applicationTableDiv: HTMLDivElement;
    measurementTableDiv: HTMLDivElement;
    experimentTableDiv: HTMLDivElement;

    constructor(app: JupyterLab) {
        super(app, project_widget_id, 'Project');
    }

    /*
     * Requests new data from TAU Commander and updates the table to display that data.
     */
    update(): void {
        this.clear();
        this.kernels.get_project().then(project_entries => {
            this.update_handler(project_entries, false, 'Hash');
        });
    }

}
