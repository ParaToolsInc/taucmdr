import {
    JupyterLab
} from '@jupyterlab/application';

import {
    NotebookPanel
} from "@jupyterlab/notebook";

import {
    TauCmdrPaneWidget
} from "./tam_widget";

import {
    Table
} from "./table";

import {
    Kernels
} from "./kernels";

import {
    showErrorMessage
} from "./error"

export const analysis_widget_id = 'taucmdr_analysis_sidebar';

export class AnalysisSidebarWidget extends TauCmdrPaneWidget {

    get_table_names() : Array<string> {
        return ['analysisTableDiv'];
    }

    analysisTableDiv : HTMLDivElement;

    constructor(app: JupyterLab) {
        super(app, analysis_widget_id, 'Analysis');
        this.removeClass('taucmdr_tam_pane');
        this.addClass('taucmdr_tam_sidebar');
        this.mainContent.className = 'sidebar-content';
        this.tableClassName = 'sidebar';
    }

    protected insert_cell(text: string) {
        if(this.app.shell.activeWidget instanceof NotebookPanel) {
            let notebookPanel = this.app.shell.activeWidget as NotebookPanel;
            let cell = notebookPanel.model.contentFactory.createCodeCell({});
            notebookPanel.model.cells.insert(notebookPanel.notebook.activeCellIndex + 1, cell);
        } else {
            showErrorMessage("No notebook is active",
                "An analysis can only be added to a notebook, but a notebook is not active.").then(()=>{});
        }
    }

    protected on_select_analysis(event: MouseEvent) : void {
        let id = (event.target as HTMLElement).id;
        console.log(`Should run analysis ${id}`);

    }

    /*
     * Requests new data from TAU Commander and updates the table to display that data.
     */
    update(): void {
        this.clear();
        this.kernels.get_analyses_as_table().then(project_entries => {
            console.log(project_entries);
            this.update_handler(project_entries, Table.SelectionType.Single, 'Name');
        });
    }

    protected update_handler(entries : Array<Kernels.JSONResult>, selectable : Table.SelectionType,
                             primary_key : string) : void {
        entries.forEach(entry => {
            this.update_table(this[entry['model']+'TableDiv'], entry['model'],
                entry['rows'], entry['headers'], selectable, primary_key, event => {
                    this.on_select_analysis(event);
                });
        });
    }

}
