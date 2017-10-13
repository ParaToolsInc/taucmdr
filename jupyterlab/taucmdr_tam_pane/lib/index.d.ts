import { Widget } from '@phosphor/widgets';
import { JupyterLab, JupyterLabPlugin } from '@jupyterlab/application';
import { Message } from '@phosphor/messaging';
import { Kernels } from "./kernels";
import '../style/index.css';
export declare class TAMPaneWidget extends Widget {
    app: JupyterLab;
    kernels: Kernels;
    mainContent: HTMLDivElement;
    readonly table_names: string[];
    projectTableDiv: HTMLDivElement;
    targetTableDiv: HTMLDivElement;
    applicationTableDiv: HTMLDivElement;
    measurementTableDiv: HTMLDivElement;
    experimentTableDiv: HTMLDivElement;
    [propname: string]: any;
    constructor(app: JupyterLab);
    protected onAfterAttach(msg: Message): void;
    protected onBeforeDetach(msg: Message): void;
    update_table(div: HTMLDivElement, model: string, rows: Array<Kernels.JSONResult>, fields: Array<string>): void;
    update(): void;
    display(): void;
}
export declare let defaultTAMPane: TAMPaneWidget;
declare const extension: JupyterLabPlugin<void>;
export default extension;
