import { Widget } from '@phosphor/widgets';
import { JupyterLab, JupyterLabPlugin } from '@jupyterlab/application';
import { Message } from '@phosphor/messaging';
import { Kernels } from "./kernels";
import '../style/index.css';
export declare class TAMPaneWidget extends Widget {
    app: JupyterLab;
    kernels: Kernels;
    mainContent: HTMLDivElement;
    get_table_names(): Array<string>;
    projectTableDiv: HTMLDivElement;
    targetTableDiv: HTMLDivElement;
    applicationTableDiv: HTMLDivElement;
    measurementTableDiv: HTMLDivElement;
    experimentTableDiv: HTMLDivElement;
    [propname: string]: any;
    constructor(app: JupyterLab);
    protected onAfterAttach(msg: Message): void;
    protected onBeforeDetach(msg: Message): void;
    clear(): void;
    protected update_table(div: HTMLDivElement, model: string, rows: Array<Kernels.JSONResult>, fields: Array<string>): void;
    protected update_handler(entries: Array<Kernels.JSONResult>): void;
    update(): void;
    display(): void;
}
export declare class ExperimentPaneWidget extends TAMPaneWidget {
    get_table_names(): Array<string>;
    trialTableDiv: HTMLDivElement;
    constructor(app: JupyterLab);
    update(): void;
}
export declare let defaultTAMPane: TAMPaneWidget;
export declare let defaultExperimentPane: ExperimentPaneWidget;
declare const extension: JupyterLabPlugin<void>;
export default extension;
