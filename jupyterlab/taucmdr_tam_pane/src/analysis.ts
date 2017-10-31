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

    protected insert_cell(text: Array<string>) {
        if(this.app.shell.currentWidget instanceof NotebookPanel) {
            let notebookPanel = this.app.shell.currentWidget as NotebookPanel;
            let cellOptions = {cell: {source: text, metadata: {trusted: true}}};
            let cell = notebookPanel.model.contentFactory.createCodeCell(cellOptions as any);
            notebookPanel.model.cells.insert(notebookPanel.notebook.activeCellIndex + 1, cell);
            notebookPanel.notebook.activeCellIndex++;
        } else {
            throw new Error("No notebook is active");
        }
    }

    protected on_select_analysis(event: MouseEvent) : void {
        let id = (event.target as HTMLElement).id;
        console.log(`Should run analysis ${id}`);
        let selected_trials = window.defaultExperimentPane.table.get_selected();
        this.kernels.get_analysis_cells(id, selected_trials).then(response => {
            let analysis_cells : Array<Kernels.JSONResult> = response.cells;
            analysis_cells.forEach(analysis_cell => {
                this.insert_cell([analysis_cell.source]);
            });
        }, reason => {
            showErrorMessage("Unable to run analysis.", reason.toString()).then(()=>{});
        });
        this.insert_cell([id]);
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
