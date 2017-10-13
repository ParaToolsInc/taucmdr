import { Session } from '@jupyterlab/services';
export declare class Kernels {
    session: Session.ISession;
    constructor();
    protected handle_listing_command(command: string): Promise<Array<Kernels.JSONResult>>;
    get_project(): Promise<Array<Kernels.JSONResult>>;
    get_trials(): Promise<Array<Kernels.JSONResult>>;
    protected execute_kernel(kernel: string): Promise<string>;
    protected start_session(): Promise<Session.ISession>;
}
export declare namespace Kernels {
    const session_path = "taucmdr_tam_pane.ipynb";
    const getProjectKernel: string;
    const getTrialsKernel: string;
    class JSONResult {
        readonly [propname: string]: any;
    }
}
