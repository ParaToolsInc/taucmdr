import {
    SessionContext,
    ISessionContext,
    sessionContextDialogs,
} from '@jupyterlab/apputils';

import { StackedPanel } from '@lumino/widgets';
import { Message } from '@lumino/messaging';
import { ServiceManager } from '@jupyterlab/services';

import { KernelModel } from './KernelModel';
import { TableView } from './TableView';

export class WidgetApp extends StackedPanel {
    constructor(manager: ServiceManager.IManager) {
        super();


        let root = document.documentElement;
	root.style.setProperty('--tau-table-color', '#E7EAEB');
        
        this.id = 'taucmdr_body';
        this.title.iconClass = 'tau-logo-toolbar';
        this.title.label = 'Taucmdr';
        this.title.closable = true;

        this._sessionContext = new SessionContext({
            sessionManager: manager.sessions,
            specsManager: manager.kernelspecs,
            name: 'Tau Commander'
        });

        this._model = new KernelModel(this._sessionContext);
        this._tables = new TableView(this._model);

        this.addWidget(this._tables);
        void this._sessionContext
            .initialize()
            .then(async value => {
                if (value) {
                    await sessionContextDialogs.selectKernel(this._sessionContext);
                }
            })
            .catch(reason => {
                console.error(
                    `Failed to initialize the session in WidgetApp.\n${reason}`
                );
            });
    }

    get session(): ISessionContext {
        return this._sessionContext;
    }

    dispose(): void {
        this._sessionContext.dispose();
        super.dispose();
    }

    protected onCloseRequest(msg: Message): void {
        super.onCloseRequest(msg);
        this.dispose();
    }

    private _sessionContext: SessionContext;
    private _model: KernelModel;
    private _tables: TableView;

}
