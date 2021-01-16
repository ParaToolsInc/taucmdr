import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import {
  ICommandPalette,
  MainAreaWidget,
  ToolbarButton,
  SessionContext,
  sessionContextDialogs
} from '@jupyterlab/apputils';

import { Widget } from '@lumino/widgets';

import { LabIcon } from '@jupyterlab/ui-components';

import { KernelModel } from './model';

import svglogo from '../style/paratools.svg';

import { updateTable } from './kernel';

const icon = new LabIcon({
  name: 'logo:svg',
  svgstr: svglogo
});

/**
 * Initialization data for the dashboard-display extension.
 */
const extension: JupyterFrontEndPlugin<void> = {
  id: 'dashboard-display:plugin',
  autoStart: true,
  requires: [ICommandPalette],
  activate: (app: JupyterFrontEnd, palette: ICommandPalette) => {
    console.log('JupyterLab extension dashboard-display is activated!');

    const command: string = 'taucmdr:open';
    app.commands.addCommand(command, {
      label: 'Taucmdr',
      execute: () => {

        const content = new Widget()
        const widget = new MainAreaWidget({ content });
        const context = new SessionContext({
          sessionManager: app.serviceManager.sessions,
          specsManager: app.serviceManager.kernelspecs,
          name: 'Tau Commander Kernel'
        });
        const kernel = new KernelModel(context);

        void context
          .initialize()
          .then(async value => {
            if (value) {
              await sessionContextDialogs.selectKernel(context);
            }
          })
          .catch(reason => {
            console.error(
              `Failed to initialize the session.\n${reason}`
            );
          });


        const toolbarlogo = new ToolbarButton({
          icon: icon,
          onClick: () => updateTable(kernel, content.node)
        });
        toolbarlogo.id = 'logo';

        const toolbarbutton = new ToolbarButton({
          label: 'Refresh Project List',
          onClick: () => updateTable(kernel, content.node)
        });
        toolbarbutton.id = 'button';

        widget.id = 'tau_commander';
        widget.title.icon = icon;
        widget.title.label = 'TAU Commander';
        widget.title.closable = true;
        widget.toolbar.insertItem(0, 'logo', toolbarlogo);
        widget.toolbar.insertItem(1, 'refresh_button', toolbarbutton);

        if (!widget.isAttached) {
          app.shell.add(widget, 'main');
        }

        app.shell.activateById(widget.id);
      }
    });

    palette.addItem({ command, category: 'TAU Commander' });
  }
};

export default extension;
