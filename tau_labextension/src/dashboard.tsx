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
  TrialTable
} from './tables';

import {
  newTargetDialog,
  newApplicationDialog,
  newMeasurementDialog,
  newExperimentDialog,
  
  errorDialog
} from './dialogs';

import * as ReactDOM from 'react-dom';

export class Dashboard extends Widget {
  constructor(options: Dashboard.IOptions) {
    super();
    this.addClass('tau-TauDashboard');

    this._projectName = options.project.label;
    this._project = options.project.data
    this._kernelSession = options.kernelSession;
    this._sidebar = options.sidebar;

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

    let toolbar = options.toolbar;
    toolbar.addItem(
      'new target',
      new ToolbarButton({
        label: 'New Target',
        className: 'tau-dashboardToolbar-button',
        onClick: () => {
          const dialog = newTargetDialog();
          dialog.launch()
            .then(response => {
              if (response.button.label == 'Submit') {
                let name = response.value!.name;
                let hostOS = response.value!.hostOS;
                let hostArch = response.value!.hostArch;
                let hostCompiler = response.value!.hostCompiler;
                let mpiCompiler = response.value!.mpiCompiler;
                let shmemCompiler = response.value!.shmemCompiler;
                this._kernelExecute(`new_target('${this._projectName}', '${name}', '${hostOS}', '${hostArch}', '${hostCompiler}', '${mpiCompiler}', '${shmemCompiler}')`)
                  .then((result) => {
                    if (result) {
                      this._updateProject(this._projectName);
                    }
                  });
              }
              dialog.dispose(); 
            });
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
          const dialog = newApplicationDialog();
          dialog.launch()
            .then(response => {
              if (response.button.label == 'Submit') {
                let name = response.value!.name;
                let linkage = response.value!.linkage;
                let openMP = response.value!.openMP;
                let pThreads = response.value!.pThreads;
                let tbb = response.value!.tbb;
                let mpi = response.value!.mpi;
                let cuda = response.value!.cuda;
                let openCL = response.value!.openCL;
                let shmem = response.value!.shmem;
                let mpc = response.value!.mpc;
                this._kernelExecute(`new_application('${this._projectName}', '${name}', '${linkage}', '${openMP}', '${pThreads}', '${tbb}', '${mpi}', '${cuda}', '${openCL}', '${shmem}', '${mpc}')`)
                  .then((result) => {
                    if (result) {
                      this._updateProject(this._projectName);
                    }
                  });
              }
              dialog.dispose(); 
            });
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
          const dialog = newMeasurementDialog();
          dialog.launch()
            .then(response => {
              if (response.button.label == 'Submit') {
                let name = response.value!.name;
                let profile = response.value!.profile;
                let trace = response.value!.trace;
                let sample = response.value!.sample;
                let sourceInst = response.value!.sourceInst;
                let compilerInst = response.value!.compilerInst;
                let openMP = response.value!.openMP;
                let cuda = response.value!.cuda;
                let io = response.value!.io;
                let mpi = response.value!.mpi;
                let shmem = response.value!.shmem;
                this._kernelExecute(`new_measurement('${this._projectName}', '${name}', '${profile}', '${trace}', '${sample}', '${sourceInst}', '${compilerInst}', '${openMP}', '${cuda}', '${io}', '${mpi}', '${shmem}')`)
                  .then((result) => {
                    if (result) {
                      this._updateProject(this._projectName);
                    }
                  });
              }
              dialog.dispose(); 
            });
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
          const dialog = newExperimentDialog(this._project);
          dialog.launch()
            .then(response => {
              if (response.button.label == 'Submit') {
                let name = response.value!.name;
                let target = response.value!.target;
                let application = response.value!.application;
                let measurement = response.value!.measurement;
                this._kernelExecute(`new_experiment('${this._projectName}', '${name}', '${target}', '${application}', '${measurement}')`)
                  .then((result) => {
                    if (result) {
                      this._updateProject(this._projectName);
                    }
                  });
              }
              dialog.dispose(); 
            });
        },
        tooltip: 'New Experiment'
      })
    );

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
          if (msg.header.msg_type == 'stream') {
            let content = (msg as KernelMessage.IStreamMsg).content;
            let output = content.text;
            this._sidebar.consoleStream.push(output);
            this._sidebar.update();
          }
  
          if (msg.header.msg_type == 'error') {
            let content = (msg as KernelMessage.IErrorMsg).content;
            let output = content.ename + ': ' + content.evalue; 
            let dialog = errorDialog(output);
            dialog.launch().then(response => {
              console.log(output);
            });
          }
  
          if (msg.header.msg_type == 'execute_result') {
            let data = (msg as KernelMessage.IDisplayDataMsg).content.data;
            let output = (data['text/plain'] as string) || '';
            let jsonOutput = JSON.parse(output.replace(/'/g, ''));
            if (jsonOutput.status == 'failure') {
              if (jsonOutput.message.includes('Error in')) {
                let dialog = errorDialog(jsonOutput.message + ': ' + 'This name may already be taken. Please try a different name.');
                dialog.launch();
              } else {
                let dialog = errorDialog(jsonOutput.message);
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
        experiments={this._project.experiments}
      />,
      this._experimentDisplay.node
    );
 
    ReactDOM.render(
      <TrialTable
        projectName={this._projectName}
        trials={this._project.experiments}  
      />,
      this._trialDisplay.node
    );
  
    console.log(this._project);
    console.log(this._selectedExperiment);
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
  private _selectedExperiment: any = null;
  private _project: any;
  private _kernelSession: Session.ISessionConnection | null | undefined;
  private _sidebar: Sidebar;
}

export namespace Dashboard {
  
  export interface IOptions {
    project: IDashboardItem;
    kernelSession: Session.ISessionConnection | null | undefined;
    sidebar: Sidebar;
    toolbar: Toolbar;
  }
}


