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

import CSS from 'csstype';

const pageStyle: CSS.Properties = {
    display: 'block',
    overflow: 'auto',
    height: '100%',
};

const bodyStyle: CSS.Properties = {
    padding: '0% 5% 5% 5%', 
};

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
            <div style={pageStyle}>

                <UseSignal signal={this._projectChanged}>
                    {() => (
                        <OptionToolbar model={this._model} onSetProject={this.handleProject} project={this._project}/>
                    )}
                </UseSignal>

                <UseSignal signal={this._model.stateChanged}>
                    {() => (
                        <div style={bodyStyle}>
                            <ProjectTable key="project" output={this._model.output} onSetProject={this.handleProject}/>
                            <UseSignal signal={this._projectChanged}>
                                {() => (
                                    <div>
                                        <TargetTable key="target" output={this._model.output} project={this._project}/>
                                        <ApplicationTable key="application" output={this._model.output} project={this._project}/>
                                        <MeasurementTable key="measurement" output={this._model.output} project={this._project}/>
                                        <ExperimentTable key="experiment" output={this._model.output} project={this._project}/>
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



         


