import {
  Widget,
  PanelLayout
} from '@lumino/widgets';

import {
  Sidebar,
  IDashboardItem
} from './sidebar';

import {
  Toolbar,
  ToolbarButton
} from '@jupyterlab/apputils';

import {
  Session,
  KernelMessage
} from '@jupyterlab/services';

import {
  TargetTable,
  ApplicationTable,
  MeasurementTable,
  ExperimentTable,
  TrialTable,
  IPlotlyDisplayItem
} from './tables';

import {
  newTargetDialog,
  newApplicationDialog,
  newMeasurementDialog,
  newExperimentDialog,
  errorDialog
} from './dialogs';

import * as ReactDOM from 'react-dom';

const regexpTime = /\[TAU\] (\d+).\d seconds [\/-|\\-]\[CPU: (\d+).\d [^\]]*]/gm;
const regexpDownload = /\[TAU\] Downloading: (\d+).\d seconds [\/\\-|-]\[CPU: (\d+).\d/gm;
const regexpExtract = /\[TAU\] Extracting: (\d+).\d seconds [\/\\-|-] \[(\d+).\d%/gm;
const regexpExtractArchive = /\[TAU\] Extracting archive: (\d+).\d seconds [\/\\-|-]+/gm;

export class Dashboard extends Widget {
  constructor(options: Dashboard.IOptions) {
    super();
    this.addClass('tau-TauDashboard');

    this._projectName = options.project.label;
    this._project = options.project.data
    this._kernelSession = options.kernelSession;
    this._sidebar = options.sidebar;
    this._openDisplayCommand = options.openDisplayCommand;

    const layout = (this.layout = new PanelLayout());

    this._updateProject = (projectName: string) => {
      this._kernelExecute('get_all_projects()')
        .then((result) => {
          if (result) {
            this._project = result.data[projectName];
            this.update();
            this._sidebar.refresh();
          }
        });
    }

    const toolbar = options.toolbar;
    toolbar.addItem(
      'refresh',
      new ToolbarButton({
        label: 'Refresh',
        className: 'tau-dashboardToolbar-button',
        onClick: () => {
          this._updateProject(this._projectName);
        },
        tooltip: 'New Target'
      })
    );

    toolbar.addItem(
      'new target',
      new ToolbarButton({
        label: 'New Target',
        className: 'tau-dashboardToolbar-button',
        onClick: () => {
          const props = {
            projectName: this._projectName,
            kernelExecute: this._kernelExecute,
            updateProject: this._updateProject
          };
          newTargetDialog(props);
        },
        tooltip: 'New Target'
      })
    );

    toolbar.addItem(
      'new application',
      new ToolbarButton({
        label: 'New Application',
        className: 'tau-dashboardToolbar-button',
        onClick: () => {
          const props = {
            projectName: this._projectName,
            kernelExecute: this._kernelExecute,
            updateProject: this._updateProject
          };
          newApplicationDialog(props);
        },
        tooltip: 'New Application'
      })
    );

    toolbar.addItem(
      'new measurement',
      new ToolbarButton({
        label: 'New Measurement',
        className: 'tau-dashboardToolbar-button',
        onClick: () => {
          const props = {
            projectName: this._projectName,
            kernelExecute: this._kernelExecute,
            updateProject: this._updateProject
          };
          newMeasurementDialog(props);
        },
        tooltip: 'New Measurement'
      })
    );

    toolbar.addItem(
      'new experiment',
      new ToolbarButton({
        label: 'New Experiment',
        className: 'tau-dashboardToolbar-button',
        onClick: () => {
          const props = {
            project: this._project,
            projectName: this._projectName,
            kernelExecute: this._kernelExecute,
            updateProject: this._updateProject
          };
          newExperimentDialog(props);
        },
        tooltip: 'New Experiment'
      })
    );

    this._setExperiment = (experimentName: string | null) => {
      this._selectedExperiment = experimentName;
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
            if (this._sidebar.console.isHidden) {
              this._sidebar.console.show();
              this._sidebar.consoleClearButton.show();
              this._sidebar.splitter.setRelativeSizes([0.5,0.5])
            }

            const stream = this._sidebar.consoleStream;
            const prev = stream[stream.length - 1];
            if (prev && output.match(regexpTime) && prev.match(regexpTime)) {
              stream.pop()
            }

            if (prev && output.match(regexpDownload) && prev.match(regexpDownload)) {
              stream.pop()
            }

            if (prev && output.match(regexpExtract) && prev.match(regexpExtract)) {
              stream.pop()
            }

            if (prev && output.match(regexpExtractArchive) && prev.match(regexpExtractArchive)) {
              stream.pop()
            }

            stream.push(output);
            this._sidebar.update();
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

    this._targetDisplay = new Widget();
    this._targetDisplay.addClass('tau-Table-display');
    layout.addWidget(this._targetDisplay);

    this._applicationDisplay = new Widget();
    this._applicationDisplay.addClass('tau-Table-display');
    layout.addWidget(this._applicationDisplay);

    this._measurementDisplay = new Widget();
    this._measurementDisplay.addClass('tau-Table-display');
    layout.addWidget(this._measurementDisplay);

    this._experimentDisplay = new Widget();
    this._experimentDisplay.addClass('tau-Table-display');
    layout.addWidget(this._experimentDisplay);

    this._trialDisplay = new Widget();
    this._trialDisplay.addClass('tau-Table-display');
    layout.addWidget(this._trialDisplay);
  }

  /**
   * Handle an update request.
   */
  protected onUpdateRequest(): void {
    if (!this.isVisible) {
      return;
    }

    this._kernelExecute(`select_project("${this._projectName}")`)

    ReactDOM.render(
      <TargetTable
        projectName={this._projectName}
        kernelExecute={this._kernelExecute}
        updateProject={this._updateProject}
        targets={this._project.targets}
      />,
      this._targetDisplay.node
    );

    ReactDOM.render(
      <ApplicationTable
        projectName={this._projectName}
        kernelExecute={this._kernelExecute}
        updateProject={this._updateProject}
        applications={this._project.applications}
      />,
      this._applicationDisplay.node
    );

    ReactDOM.render(
      <MeasurementTable
        projectName={this._projectName}
        kernelExecute={this._kernelExecute}
        updateProject={this._updateProject}
        measurements={this._project.measurements}
      />,
      this._measurementDisplay.node
    );

    ReactDOM.render(
      <ExperimentTable
        project={this._project}
        projectName={this._projectName}
        kernelExecute={this._kernelExecute}
        updateProject={this._updateProject}
        setSelectedExperiment={this._setExperiment}
        experiments={this._project.experiments}
      />,
      this._experimentDisplay.node
    );

    ReactDOM.render(
      <TrialTable
        projectName={this._projectName}
        kernelExecute={this._kernelExecute}
        updateProject={this._updateProject}
        experiment={this._project.experiments[this._selectedExperiment]}
        setSelectedExperiment={this._setExperiment}
        selectedExperiment={this._selectedExperiment}
        openDisplayCommand={this._openDisplayCommand}
      />,
      this._trialDisplay.node
    );
  }

  /**
   * Rerender after showing.
   */
  protected onAfterShow(): void {
    this.update();
  }

  private _kernelExecute: (code: string) => Promise<any>;
  private _updateProject: (projectName: string) => void;
  private _targetDisplay: Widget;
  private _applicationDisplay: Widget;
  private _measurementDisplay: Widget;
  private _experimentDisplay: Widget;
  private _trialDisplay: Widget;
  private _projectName: string;
  private _setExperiment: (experimentName: string | null) => void;
  private _selectedExperiment: any = null;
  private _project: any;
  private _kernelSession: Session.ISessionConnection | null | undefined;
  private _sidebar: Sidebar;
  private _openDisplayCommand: (trialPath: IPlotlyDisplayItem) => void;
}

export namespace Dashboard {
  export interface IOptions {
    project: IDashboardItem;
    kernelSession: Session.ISessionConnection | null | undefined;
    sidebar: Sidebar;
    toolbar: Toolbar;
    openDisplayCommand: (trialPath: IPlotlyDisplayItem) => void;
  }
}
