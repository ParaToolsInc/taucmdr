import {
    Widget
} from '@phosphor/widgets';

import {
    JupyterLab
} from '@jupyterlab/application';

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

export const class_name = 'tam';

export abstract class TauCmdrPaneWidget extends Widget {
    app: JupyterLab;
    kernels : Kernels;

    mainContent: HTMLDivElement;

    /*
     * Returns the names of the tables the widget is to display. The class should contain
     * variables of the same names.
     */
    abstract get_table_names() : Array<string>;

    /*
     * Requests new data from TAU Commander and updates the table to display that data.
     */
    abstract update(): void;

    [propname: string] : any;

    table: Table;

    constructor(app: JupyterLab, id: string, label: string) {
        super();

        this.kernels = new Kernels();
        this.app = app;

        this.id = id;
        this.title.label = label;
        this.title.closable = true;
        this.addClass('taucmdr_tam_pane');

        this.mainContent = document.createElement('div');
        this.mainContent.className = 'main-content';
        this.node.appendChild(this.mainContent);

        this.get_table_names().forEach(table_name => {
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
            this[table_name].innerHTML = '';
        })
    }

    /*
     * Replaces the table contents of `rows` with a new table containing headings listed in `fields` and
     * values from the JSON array `rows`.
     */
    protected update_table(div: HTMLDivElement, model: string, rows: Array<Kernels.JSONResult>, fields: Array<string>,
                           selectable : boolean, primary_key: string): void {
        this.table = new Table(rows, fields, class_name, selectable, primary_key);
        div.innerHTML = "";
        div.appendChild(document.createElement('h1').appendChild(
            document.createTextNode(model)));
        div.appendChild(this.table.get_table());
    }

    protected update_handler(entries : Array<Kernels.JSONResult>, selectable : boolean, primary_key : string) : void {
        entries.forEach(entry => {
            this.update_table(this[entry['model']+'TableDiv'], entry['model'],
                entry['rows'], entry['headers'], selectable, primary_key);
        });
    }


    display(): void {
        this.app.shell.addToMainArea(this);
    }
}
