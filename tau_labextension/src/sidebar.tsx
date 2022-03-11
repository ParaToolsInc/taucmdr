import {
  Toolbar,
  ToolbarButton,
  WidgetTracker,
} from '@jupyterlab/apputils';

import {
  Widget,
  PanelLayout,
  SplitPanel,
  Panel
} from '@lumino/widgets';

import {
  Session,
  KernelMessage
} from '@jupyterlab/services';

import {
  Button,
  addIcon,
  clearIcon,
  refreshIcon,
  tableRowsIcon
} from '@jupyterlab/ui-components';

import {
  Icon
} from '@blueprintjs/core';

import {
  newProjectDialog,
  copyProjectDialog,
  editProjectDialog,
  deleteProjectDialog,
  errorDialog
} from './dialogs';

import * as React from 'react';
import * as ReactDOM from 'react-dom';

/**
 * A Widget for tau project management.
 */
export class Sidebar extends Widget {
  /**
   * Create a new Tau sidebar.
   */
  constructor(options: Sidebar.IOptions) {
    super();
    this.addClass('tau-TauSidebar');

    this._openDashboardCommand = options.openDashboardCommand;
    this._kernelSession = options.kernelSession;

    const layout = (this.layout = new PanelLayout());
    this._splitter = new SplitPanel({ orientation: 'vertical' });

    // A function to initialize the ipython kernel
    this._updateConnected = () => {
      ['%reset -f',
       'import os',
       'import sys',
       'package_dir = os.path.join(os.environ.get("HOME"), "src/packages")',
       'sys.path.insert(0, package_dir)',
       'from taucmdr.kernel import *'
      ].map((code) => {
        this._kernelExecute(code);
      });

      this._kernelExecute('connect()')
        .then((result) => {
          if (result) {
            this._connected = true;
            this.update();
          }
        });
    }

    // A function to update the current projects
    this._updateProjects = () => {
      this._kernelExecute('get_all_projects()')
        .then((result) => {
          if (result) {
            this._projects = result.data;
          }
          this.update();
        });
    }

    // A function to select a project
    this._selectProject = (projectName: string) => {
      this._kernelExecute(`select_project("${projectName}")`)
    }

    // A function to create a project
    this._createProject = () => {
      const props = {
        kernelExecute: this._kernelExecute,
        updateProjects: this._updateProjects
      };
      newProjectDialog(props);
    }

    // A function to edit a project
    this._editProject = (projectName: string) => {
      const props = {
        projectName,
        kernelExecute: this._kernelExecute,
        updateProjects: this._updateProjects,
        tracker: options.tracker
      };
      editProjectDialog(props);
    }

    // A function to copy a project
    this._copyProject = (projectName: string) => {
      const props = {
        projectName,
        kernelExecute: this._kernelExecute,
        updateProjects: this._updateProjects
      };
      copyProjectDialog(props);
    }

    // A function to delete a project
    this._deleteProject = (projectName: string) => {
      const props = {
        projectName,
        kernelExecute: this._kernelExecute,
        updateProjects: this._updateProjects,
        tracker: options.tracker,
      };
      deleteProjectDialog(props);
    }

    /**
     * Execute kernel commands (python3)
     */
    this._kernelExecute = (code: string) => {
      if (!this._kernelSession) {
        return new Promise((resolve, reject) => {
          resolve('Kernel Failure');
        });
      }

      const kernel = this._kernelSession!.kernel;
      const content: KernelMessage.IExecuteRequestMsg['content'] = {
        store_history: false,
        code
      };

      return new Promise<string>((resolve, _) => {
        const future = kernel!.requestExecute(content);
        future.onIOPub = msg => {
          if (msg.header.msg_type === 'stream') {
            const message = (msg as KernelMessage.IStreamMsg).content;
            const output = message.text;
            if (this._console.isHidden) {
              this._console.show();
              this._consoleClearButton.show();
              this._splitter.setRelativeSizes([0.5,0.5])
            }
            this._consoleStream.push(output);
            this.update();
          }

          if (msg.header.msg_type === 'error') {
            const message = (msg as KernelMessage.IErrorMsg).content;
            const output = message.ename + ': ' + message.evalue;
            const dialog = errorDialog(output);
            dialog.launch().then(response => {
              console.log(output);
            });
          }

          if (msg.header.msg_type === 'execute_result') {
            const message = (msg as KernelMessage.IDisplayDataMsg).content.data;
            const output = (message['text/plain'] as string) || '';
            const jsonOutput = JSON.parse(output.replace(/'/g, ''));
            if (jsonOutput.status === 'failure') {
              if (jsonOutput.message.includes('Error in')) {
                const dialog = errorDialog(jsonOutput.message + ': ' + 'This name may already be taken. Please try a different name.');
                dialog.launch();
              } else {
                const dialog = errorDialog(jsonOutput.message);
                dialog.launch();
              }
            } else {
              resolve(jsonOutput);
            }
          }
        };
      });
    }

    this._updateConnected();
    this._updateProjects();

    this._toolbar = new Toolbar<Widget>();
    this._toolbar.addClass('tau-TauSidebar-toolbar')

    const toolbarLabel = new Widget();
    toolbarLabel.node.textContent = 'Projects';
    toolbarLabel.addClass('tau-TauSidebar-toolbar-label');
    this._toolbar.addItem('label', toolbarLabel);

    this._toolbar.addItem(
      'refresh',
      new ToolbarButton({
        icon: refreshIcon,
        onClick: this._updateProjects,
        tooltip: 'Refresh Project List'
      })
    );

    this._toolbar.addItem(
      'new project',
      new ToolbarButton({
        icon: addIcon,
        onClick: this._createProject,
        tooltip: 'Create New Project'
      })
    );

    this._consoleClearButton = new ToolbarButton({
      icon: clearIcon,
      onClick: () => {
        this._consoleStream = [];
        this.update();
      },
      tooltip: 'Clear Console'
    });
    this._consoleClearButton.hide();

    this._toolbar.addItem(
      'toggle console',
      new ToolbarButton({
        icon: tableRowsIcon,
        onClick: () => {
          if (this._console.isHidden) {
            this._console.show()
            this._consoleClearButton.show();
            this._splitter.setRelativeSizes([0.5,0.5])
          } else {
            this._console.hide();
            this._consoleClearButton.hide();
          }
        },
        tooltip: 'Toggle Console'
      })
    );

    this._toolbar.addItem(
      'clear console',
      this._consoleClearButton
    );

    layout.addWidget(this._splitter);
    const body = new Panel();

    this._splitter.addClass('tau-Splitter');
    body.addClass('tau-SidebarBody');
    body.addWidget(this._toolbar);

    this._display = new Widget();
    this._display.addClass('tau-ListingDisplay');
    body.addWidget(this._display);
    this._splitter.addWidget(body);

    this._console = new Widget();
    this._console.addClass('tau-StreamConsole');
    this._console.hide();
    this._splitter.addWidget(this._console);
  }


  /**
   * Handle an update request.
   */
  protected onUpdateRequest(): void {
    if (!this.isVisible) {
      return;
    }

    if (!this._connected) {
      if (!this._toolbar.isHidden) {
        this._toolbar.hide();
      }
      ReactDOM.render(
        <SidebarFailure
          refresh={this._updateConnected}
        />,
        this._display.node
      );

    } else {
      if (this._toolbar.isHidden) {
        this._toolbar.show();
      }
      ReactDOM.render(
        <ProjectListing
          openDashboardCommand={this._openDashboardCommand}
          projects={this._projects}
          selectProject={this._selectProject}
          copyProject={this._copyProject}
          editProject={this._editProject}
          deleteProject={this._deleteProject}
        />,
        this._display.node
      );

      ReactDOM.render(
        <ConsoleOutput
         stream={this._consoleStream}
        />,
        this._console.node
      );
      this._console.node.scrollTop = this._console.node.scrollHeight - this._console.node.clientHeight;
    }
  }

  // A public function to update Projects
  public refresh(): void {
    this._updateProjects();
  }

  get consoleStream(): string[] {
    return this._consoleStream;
  }

  get consoleClearButton(): ToolbarButton {
    return this._consoleClearButton;
  }

  get splitter(): SplitPanel {
    return this._splitter;
  }

  get projects(): Sidebar.ProjectList {
    return this._projects;
  }

  get console(): Widget {
    return this._console;
  }

  /**
   * Rerender after showing.
   */
  protected onAfterShow(): void {
    this.update();
  }

  private _createProject: () => void;
  private _updateConnected: () => void;
  private _updateProjects: () => void;
  private _selectProject: (project: string) => void;
  private _copyProject: (project: string) => void;
  private _editProject: (project: string) => void;
  private _deleteProject: (project: string) => void;
  private _kernelExecute: (code: string) => Promise<any>;

  private _splitter: SplitPanel;
  private _projects: Sidebar.ProjectList = {};
  private _connected: boolean | undefined = false;
  private _consoleStream: string[] = [];
  private _kernelSession: Session.ISessionConnection | null | undefined;
  private _toolbar: Toolbar<Widget>;
  private _consoleClearButton: ToolbarButton;
  private _display: Widget;
  private _console: Widget;
  private _openDashboardCommand: (project: IDashboardItem) => void;
}

export namespace Sidebar {

  export interface IOptions {
    openDashboardCommand: (project: IDashboardItem) => void;
    kernelSession: Session.ISessionConnection | null | undefined;
    tracker: WidgetTracker;
  }

  interface Property {
    [prop: string]: string | number | boolean
  }

  interface Field {
    [field: string]: Property
  }

  export interface Project {
    [name: string]: Field
  }

  export interface ProjectList {
    [projects: string]: Project
  }

}

export interface IDashboardItem {
  [key: string]: any;
  data: Sidebar.Project;
}

const ProjectListing = (props: ProjectListingProps) => {
  const listing = Object.keys(props.projects).map(project => {
    return (
      <li className='tau-ProjectListing-item' key={project}>
        <p className='tau-ProjectListing-item-name'>{ project }</p>
        <div className='tau-ProjectListing-item-buttons'>
          <Button
            onClick={() => {
                props.openDashboardCommand({
                  label: project,
                  data: props.projects[project]
                });
                props.selectProject(project)
            }}
            className='tau-ProjectListingItem-button'>
            <Icon icon='application'/>
          </Button>
          <Button
            onClick={() => props.copyProject(project)}
            className='tau-ProjectListingItem-button'
          >
            <Icon icon='duplicate'/>
          </Button>
          <Button
            onClick={() => props.editProject(project)}
            className='tau-ProjectListingItem-button'
          >
            <Icon icon='edit'/>
          </Button>
          <Button
            onClick={() => props.deleteProject(project)}
            className='tau-ProjectListingItem-button'
          >
            <Icon icon='cross'/>
          </Button>
        </div>
      </li>
    );
  });

  return (
    <ul className='tau-ProjectListing-list'>
      {listing}
    </ul>
  );
}

interface ProjectListingProps {
  openDashboardCommand: (project: IDashboardItem) => void;
  projects: Sidebar.ProjectList;
  selectProject: (project: string) => void;
  copyProject: (project: string) => void;
  editProject: (project: string) => void;
  deleteProject: (project: string) => void;
}

const SidebarFailure = (props: SidebarFailureProps) => {
  return (
    <div className='tau-SidebarFailure'>
      <span className='tau-SidebarFailure-title'>
        TAU not found
      </span>
      <span className='tau-SidebarFailure-detail'>
        To connect a display, include the path of TAU in
        your $PATH environment variable. If you are still
        unable to connect, please reach out to cfd@paratools.com
      </span>
      <Button className='tau-SidebarFailure-refresh'
        onClick={props.refresh}
      >
        Refresh
      </Button>
    </div>
  );
}

interface SidebarFailureProps {
  refresh: () => void;
}

const ConsoleOutput = (props: ConsoleOutputProps) => {
  const data = props.stream.map((line, idx) => {
    return (
      <li className='tau-StreamConsole-item' key={idx}>
        {idx+1} <code>{ line }</code>
      </li>
    );
  });

  return (
    <ul className='tau-StreamConsole-list'>
      {data}
    </ul>
  );
}

interface ConsoleOutputProps {
  stream: string[];
}
