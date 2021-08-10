import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { ICommandPalette } from '@jupyterlab/apputils';

import { WidgetApp } from './App';

const extension: JupyterFrontEndPlugin<void> = {
  id: 'tau_commander:plugin',
  autoStart: true,
  requires: [ICommandPalette],
  activate: (app: JupyterFrontEnd, palette: ICommandPalette) => {

    const command = 'taucmdr:open';
    const category = 'Tau Commander';
    const manager = app.serviceManager;

    async function createWidget(): Promise<WidgetApp> {
        const widget = new WidgetApp(manager);
        app.shell.add(widget, 'main');
        return widget;
    }

    app.commands.addCommand(command, {
        label: 'TAU Commander',
        execute: createWidget        
    });

    palette.addItem({ 
        command: command, 
        category: category
    });
  }
};

export default extension;
