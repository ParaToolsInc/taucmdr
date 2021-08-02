import React from 'react';

import { ReactWidget, UseSignal } from '@jupyterlab/apputils';
import { Signal } from '@lumino/signaling';
import { KernelModel } from './KernelModel';

import { OptionToolbar } from './components/OptionToolbarComponent';
import { ProjectTable } from './components/ProjectTableComponent';
import { TargetTable } from './components/TargetTableComponent';
import { ApplicationTable } from './components/ApplicationTableComponent';
import { MeasurementTable } from './components/MeasurementTableComponent';
import { ExperimentTable } from './components/ExperimentTableComponent';

export class TableView extends ReactWidget {
    constructor(model: KernelModel) {
        super();
        this._model = model;
        this.handleProject = this.handleProject.bind(this);
    }

    handleProject(name: string | null) {
        this._project = name;
        this._projectChanged.emit();
    }

    protected render() {
        return (
            <div className='tau-extension-body'>
                <UseSignal signal={this._model.stateChanged}>
                    {() => (
                        <UseSignal signal={this._projectChanged}>
                            {() => (
                                <OptionToolbar model={this._model} output={this._model.output} onSetProject={this.handleProject} project={this._project}/>
                            )}
                        </UseSignal>
                    )}
                </UseSignal>
                <UseSignal signal={this._model.stateChanged}>
                    {() => (
                        <div className='tau-table-body'>
                            <ProjectTable key="project" model={this._model} output={this._model.output} onSetProject={this.handleProject}/>
                            <UseSignal signal={this._projectChanged}>
                                {() => (
                                    <div>
                                        <TargetTable key="target" model={this._model} output={this._model.output} project={this._project}/>
                                        <ApplicationTable key="application" model={this._model} output={this._model.output} project={this._project}/>
                                        <MeasurementTable key="measurement" model={this._model} output={this._model.output} project={this._project}/>
                                        <ExperimentTable key="experiment" model={this._model} output={this._model.output} project={this._project}/>
                                    </div>
                                )}
                            </UseSignal>
                       </div>
                    )}
                </UseSignal>
            </div>
        );
    }

    private _model: KernelModel;
    private _project: string | null = null;
    private _projectChanged = new Signal<TableView, void>(this);
}
