import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import {
  SessionContext,
  ICommandPalette,
  MainAreaWidget,
  WidgetTracker,
  Toolbar
} from '@jupyterlab/apputils';

import {
  Session,
  ServiceManager
} from '@jupyterlab/services';

import {
  fileIcon
} from '@jupyterlab/ui-components';

import {
  Sidebar,
  IDashboardItem
} from './sidebar';

import {
  Dashboard
} from './dashboard';

import {
  IPlotlyDisplayItem
} from './tables';

import {
  PlotlyDisplay
} from './display';

const PLUGIN_ID = 'tau-labextension:plugin';
const TAU_KERNEL_PATH = 'TAUKernel';

namespace CommandIDs {
  export const launchDashboard = 'tau:launch-dashboard';
  export const launchDisplay = 'tau:launch-display';
}

const plugin: JupyterFrontEndPlugin<void> = {
  activate,
  id: PLUGIN_ID,
  requires: [
    ICommandPalette
  ],
  autoStart: true
};

export default plugin;

async function activate(
  app: JupyterFrontEnd,
  palette: ICommandPalette
): Promise<void> {

  const { serviceManager, shell } = app;

  // Create the Tau Kernel
  let kernelSession: Session.ISessionConnection | null | undefined;
  kernelSession = await Private.initKernel(serviceManager);

  const tracker = new WidgetTracker({
    namespace: 'dashboards'
  });

  // Create the Tau sidebar
  const sidebar = new Sidebar({
      openDashboardCommand: (project: IDashboardItem) => {
        app.commands.execute(CommandIDs.launchDashboard, project);
      },
      kernelSession,
      tracker
  });
  sidebar.id = 'tau-sidebar';
  sidebar.title.iconClass = 'tau-TauLogo';
  sidebar.title.caption = 'Tau';
  shell.add(sidebar, 'left', { rank: 300 });

  // Add Dashboard Launch command
  app.commands.addCommand(CommandIDs.launchDashboard, {
    label: (project) => `Run ${project['label']} Dashboard`,
    execute: (project) => {

      const exists = tracker.find((widgetObj) => {
        return widgetObj.id === `project-${project['label']}`;
      });

      if (exists) {
        shell.activateById(exists.id);
        return;
      }

      const toolbar = new Toolbar();
      const content = new Dashboard({
        project: project as IDashboardItem,
        kernelSession,
        sidebar,
        toolbar,
        openDisplayCommand: (trialPath: IPlotlyDisplayItem) => {
          app.commands.execute(CommandIDs.launchDisplay, trialPath);
        }
      });

      const widget = new MainAreaWidget({
        content,
        toolbar
      });

      widget.id = `project-${project['label']}`;
      widget.title.icon = fileIcon;
      widget.title.label = `${project['label']} Dashboard`;
      widget.title.closable = true;
      tracker.add(widget);

      if (!widget.isAttached) {
        // Attach the widget to the main work area if it's not there
        shell.add(widget, 'main');
      }
      // Activate the widget
      shell.activateById(widget.id);
    }
  });


  app.commands.addCommand(CommandIDs.launchDisplay, {
    label: (trialPath) => `Run ${trialPath['project']} Display`,
    execute: (trialPath) => {

      const exists = tracker.find((widgetObj) => {
        return widgetObj.id === `project-${trialPath['project']}-${trialPath['experiment']}-${trialPath['trial']}`;
      });

      if (exists) {
        shell.activateById(exists.id);
        return;
      }

      const content = new PlotlyDisplay({
        trialPath
      });
      const widget = new MainAreaWidget({
        content
      });

      widget.id = `project-${trialPath['project']}-${trialPath['experiment']}-${trialPath['trial']}`;
      widget.title.icon = fileIcon;
      widget.title.label = `Trial ${trialPath['trial']} Display`;
      widget.title.closable = true;
      tracker.add(widget);

      if (!widget.isAttached) {
        // Attach the widget to the main work area if it's not there
        shell.add(widget, 'main');
      }
      // Activate the widget
      shell.activateById(widget.id);
    }
  });
}


namespace Private {

  /*
   * Initialize a kernel on startup. If a kernel
   * already exists, then return that instance.
   * Otherwise, initilize a new kernel and return
   * that instance.
   */
  export async function initKernel(
    manager: ServiceManager
  ): Promise<Session.ISessionConnection | null | undefined> {

    let kernelSession: Session.ISessionConnection | null | undefined;

    await manager.sessions.findByPath(TAU_KERNEL_PATH)
      .then((session) => {
          if (session) {
            kernelSession = manager.sessions.connectTo({
              model: session
            });
          }
      });

    if (kernelSession) {
      return kernelSession;

    } else {
      const context = new SessionContext({
        sessionManager: manager.sessions,
        specsManager: manager.kernelspecs,
        name: 'TAU Session',
        path: TAU_KERNEL_PATH
      });

      return context
        .initialize()
        .then(async (value) => {
          await context.changeKernel({
            name: 'python3'
          });
          kernelSession = context?.session;
          return kernelSession;
        })
    }
  }
}
